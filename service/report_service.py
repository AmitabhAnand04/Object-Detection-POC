from io import BytesIO
import json, ast, requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import asyncio
import aiohttp

from database import connect_to_db
def fetch_assignment_data(assignment_id):
    query = """
    SELECT
        sa.assignment_id,
        sa.assigned_visit_date,
        sa.actual_visit_date,
        sa.status AS assignment_status,
        s.store_name,
        s.location AS store_location,
        u.full_name AS assigned_to,
        m.full_name AS assigned_by,
        sai.image_id,
        sai.image_url,
        sai.upload_time,
        sai.status AS image_status,
        sai.found_sga_photo,
        sai.auditable_photo,
        sai.purity,
        sai.chargeability,
        sai.abused,
        sai.emptyy,
        sai.detected_objects
    FROM public.storeassignments sa
    JOIN public.stores s ON sa.store_id = s.store_id
    JOIN public.users u ON sa.user_id = u.user_id
    JOIN public.users m ON sa.assigned_by = m.user_id
    LEFT JOIN public.storeassignmentimages sai ON sa.assignment_id = sai.assignment_id
    WHERE sa.assignment_id = %(assignment_id)s
    ORDER BY sai.upload_time;
    """
    _, conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(query, {'assignment_id': assignment_id})
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(colnames, row)) for row in rows]

# def create_pdf_report(assignment_id) -> bytes:
#     data = fetch_assignment_data(assignment_id)
#     if not data:
#         return None

#     assignment = data[0]
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []

#     # --- TITLE PAGE ---
#     elements.append(Paragraph(f"Store Visit Report - Assignment #{assignment_id}", styles['Title']))
#     elements.append(Spacer(1, 12))
#     elements.append(Paragraph(f"Store: {assignment['store_name']} ({assignment.get('store_location', '')})", styles['Normal']))
#     elements.append(Paragraph(f"Assigned To: {assignment['assigned_to']} (Assigned By: {assignment['assigned_by']})", styles['Normal']))
#     elements.append(Paragraph(f"Assigned Visit Date: {assignment['assigned_visit_date']}", styles['Normal']))
#     elements.append(Paragraph(f"Actual Visit Date: {assignment.get('actual_visit_date', 'Not Visited')}", styles['Normal']))
#     elements.append(Paragraph(f"Status: {assignment['assignment_status']}", styles['Normal']))
#     elements.append(Spacer(1, 20))

#     # --- OBJECT SUMMARY ---
#     object_count = {}
#     for row in data:
#         raw = row['detected_objects']
#         if raw:
#             try:
#                 if raw.startswith('"') and raw.endswith('"'):
#                     raw = raw[1:-1].replace('\\"', '"')
#                 try:
#                     objects = json.loads(raw)
#                 except:
#                     objects = ast.literal_eval(raw)
#                 for obj in objects:
#                     obj_name = obj.get('object', 'Unknown')
#                     object_count[obj_name] = object_count.get(obj_name, 0) + 1
#             except:
#                 continue

#     if object_count:
#         elements.append(Paragraph("Objects Detected Summary", styles['Heading2']))
#         table_data = [["Object", "Count"]] + [[k, v] for k, v in object_count.items()]
#         table = Table(table_data, style=TableStyle([
#             ('BACKGROUND', (0,0), (-1,0), colors.grey),
#             ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
#             ('ALIGN', (0,0), (-1,-1), 'CENTER'),
#             ('GRID', (0,0), (-1,-1), 0.5, colors.black)
#         ]))
#         elements.append(table)
#         elements.append(Spacer(1, 20))

#     elements.append(PageBreak())

#     # --- PER IMAGE DETAILS ---
#     for row in data:
#         if not row['image_id']:
#             continue
#         elements.append(Paragraph(f"Image ID: {row['image_id']}", styles['Heading2']))
#         elements.append(Paragraph(f"Uploaded: {row['upload_time']}", styles['Normal']))

#         try:
#             img_data = requests.get(row['image_url']).content
#             img = Image(BytesIO(img_data), width=200, height=400)
#             elements.append(img)
#         except:
#             elements.append(Paragraph("[Image not available]", styles['Normal']))

#         analysis_data = [
#             ["Found SGA Photo", row['found_sga_photo']],
#             ["Auditable Photo", row['auditable_photo']],
#             ["Purity", row['purity']],
#             ["Chargeability", row['chargeability']],
#             ["Abused", row['abused']],
#             ["Empty", row['emptyy']]
#         ]
#         table = Table(analysis_data, colWidths=[150, 200])
#         table.setStyle(TableStyle([
#             ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#             ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
#         ]))
#         elements.append(Spacer(1, 10))
#         elements.append(table)
#         elements.append(Spacer(1, 120))

#     doc.build(elements)
#     buffer.seek(0)
#     return buffer.getvalue()

async def fetch_image(session, url):
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                return await resp.read()
    except Exception as e:
        print(f"Image fetch failed: {url} ({e})")
    return None

async def fetch_all_images(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image(session, u) for u in urls if u]
        results = await asyncio.gather(*tasks)
        return dict(zip(urls, results))

async def create_pdf_report(assignment_id) -> bytes:
    data = fetch_assignment_data(assignment_id)
    if not data:
        return None

    assignment = data[0]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # --- TITLE PAGE ---
    elements.append(Paragraph(f"Store Visit Report - Assignment #{assignment_id}", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Store: {assignment['store_name']} ({assignment.get('store_location', '')})", styles['Normal']))
    elements.append(Paragraph(f"Assigned To: {assignment['assigned_to']} (Assigned By: {assignment['assigned_by']})", styles['Normal']))
    elements.append(Paragraph(f"Assigned Visit Date: {assignment['assigned_visit_date']}", styles['Normal']))
    elements.append(Paragraph(f"Actual Visit Date: {assignment.get('actual_visit_date', 'Not Visited')}", styles['Normal']))
    elements.append(Paragraph(f"Status: {assignment['assignment_status']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # # --- OBJECT SUMMARY (DISTINCT) ---
    # unique_objects = set()
    # for row in data:
    #     raw = row['detected_objects']
    #     if not raw:
    #         continue
    #     try:
    #         if raw.startswith('"') and raw.endswith('"'):
    #             raw = raw[1:-1].replace('\\"', '"')
    #         objects = json.loads(raw)
    #     except Exception:
    #         try:
    #             objects = ast.literal_eval(raw)
    #         except Exception:
    #             continue

    #     for obj in objects:
    #         obj_name = obj.get('object', 'Unknown')
    #         obj_label = obj.get('label', '')
    #         unique_objects.add((obj_name, obj_label))

    # if unique_objects:
    #     elements.append(Paragraph("Objects Detected Summary", styles['Heading2']))
    #     table_data = [["Object", "Label"]] + [[o, l] for o, l in sorted(unique_objects)]
    #     table = Table(table_data, style=TableStyle([
    #         ('BACKGROUND', (0,0), (-1,0), colors.grey),
    #         ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    #         ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    #         ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    #     ]))
    #     elements.append(table)
    #     elements.append(Spacer(1, 20))
    # --- OBJECT SUMMARY (DISTINCT) ---
    unique_objects = set()
    for row in data:
        raw = row['detected_objects']
        if not raw:
            continue
        try:
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1].replace('\\"', '"')
            objects = json.loads(raw)
        except Exception:
            try:
                objects = ast.literal_eval(raw)
            except Exception:
                continue

        for obj in objects:
            obj_name = obj.get('object') or "Unknown"
            obj_label = obj.get('label') or "-"
            unique_objects.add((obj_name, obj_label))

    if unique_objects:
        elements.append(Paragraph("Objects Detected Summary", styles['Heading2']))
        table_data = [["Object", "Label"]] + [
            [o, l] for o, l in sorted(unique_objects, key=lambda x: (x[0] or "", x[1] or ""))
        ]
        table = Table(table_data, style=TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    elements.append(PageBreak())

    # --- FETCH ALL IMAGES FIRST (ASYNC) ---
    image_urls = [row['image_url'] for row in data if row.get('image_id')]
    # image_map = asyncio.run(fetch_all_images(image_urls))
    image_map = await fetch_all_images(image_urls)

    # --- PER IMAGE DETAILS ---
    for row in data:
        if not row['image_id']:
            continue
        elements.append(Paragraph(f"Image ID: {row['image_id']}", styles['Heading2']))
        elements.append(Paragraph(f"Uploaded: {row['upload_time']}", styles['Normal']))

        img_bytes = image_map.get(row['image_url'])
        if img_bytes:
            try:
                img = Image(BytesIO(img_bytes), width=200, height=400)
                elements.append(img)
            except Exception:
                elements.append(Paragraph("[Image not available]", styles['Normal']))
        else:
            elements.append(Paragraph("[Image not available]", styles['Normal']))

        analysis_data = [
            ["Found SGA Photo", row['found_sga_photo']],
            ["Auditable Photo", row['auditable_photo']],
            ["Purity", row['purity']],
            ["Chargeability", row['chargeability']],
            ["Abused", row['abused']],
            ["Empty", row['emptyy']]
        ]
        table = Table(analysis_data, colWidths=[150, 200])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
        ]))
        elements.append(Spacer(1, 10))
        elements.append(table)
        elements.append(Spacer(1, 120))

    # --- LEGENDS (AT END) ---
    styles = getSampleStyleSheet()
    legend_style = styles['Normal']

    legends = [
        ("Found SGA Photo", "Indicates whether a valid SGA photo was detected.(original)"),
        ("Auditable Photo", "Whether the photo qualifies for auditing.(clarity, quality)"),
        ("Purity", "Coolers having Only Coca-cola Products (Pure), or cooler having other products also.(Impure)."),
        ("Chargeability", "How much each shelf of the cooler is filled or utilization of the shelf."),
        ("Abused", "Coolers having Zero Coca-cola Brand Product."),
        ("Empty", "Is cooler empty?")
    ]

    elements.append(PageBreak())
    elements.append(Paragraph("Legends", styles['Heading2']))

    # Wrap into Paragraphs so they wrap text correctly
    table_data = [
        [Paragraph(title, legend_style), Paragraph(desc, legend_style)]
        for title, desc in legends
    ]

    legend_table = Table(table_data, colWidths=[150, 300])
    legend_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),  # align text at top
    ]))
    elements.append(legend_table)

    # --- BUILD PDF ---
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
