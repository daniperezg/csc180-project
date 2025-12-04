import os

def generate_drawio_diagram(actors, components, flows, output_path="outputs/diagram.drawio"):
    """
    simple draw.io (diagrams.net) diagram generator.

    - Actors: rendered as ellipses on the left
    - Components: rendered as rounded rectangles on the right
    - Edges: basic connections between actors → first component, and between components
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cells = []

    # Required base cells for draw.io
    cells.append('<mxCell id="0"/>')
    cells.append('<mxCell id="1" parent="0"/>')

    current_id = 2
    vertex_ids = {}

    # Layout params
    actor_x = 40
    component_x = 260
    start_y = 40
    y_step = 90

    # Add actors as ellipses
    y = start_y
    for actor in actors:
        cell_id = str(current_id)
        current_id += 1
        vertex_ids[actor] = cell_id

        cells.append(
            f'''<mxCell id="{cell_id}" value="{actor}" style="ellipse;whiteSpace=wrap;html=1;fillColor=#e0f2fe;strokeColor=#0369a1" vertex="1" parent="1">
                    <mxGeometry x="{actor_x}" y="{y}" width="100" height="60" as="geometry"/>
                </mxCell>'''
        )
        y += y_step

    # Add components as rounded rectangles
    y = start_y
    for comp in components:
        cell_id = str(current_id)
        current_id += 1
        vertex_ids[comp] = cell_id

        cells.append(
            f'''<mxCell id="{cell_id}" value="{comp}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#15803d" vertex="1" parent="1">
                    <mxGeometry x="{component_x}" y="{y}" width="130" height="60" as="geometry"/>
                </mxCell>'''
        )
        y += y_step

    # Add simple edges:
    # 1) each actor → first component (if exists)
    if components:
        first_component = components[0]
        first_comp_id = vertex_ids.get(first_component)

        for actor in actors:
            actor_id = vertex_ids.get(actor)
            if not actor_id:
                continue

            edge_id = str(current_id)
            current_id += 1

            cells.append(
                f'''<mxCell id="{edge_id}" value="" edge="1" parent="1" source="{actor_id}" target="{first_comp_id}">
                        <mxGeometry relative="1" as="geometry"/>
                    </mxCell>'''
            )

    # 2) Link components sequentially
    for i in range(len(components) - 1):
        src = components[i]
        dst = components[i + 1]
        src_id = vertex_ids.get(src)
        dst_id = vertex_ids.get(dst)
        if not src_id or not dst_id:
            continue

        edge_id = str(current_id)
        current_id += 1

        cells.append(
            f'''<mxCell id="{edge_id}" value="" edge="1" parent="1" source="{src_id}" target="{dst_id}">
                    <mxGeometry relative="1" as="geometry"/>
                </mxCell>'''
        )

    # Build XML
    xml = f'''<mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
    <root>
        {''.join(cells)}
    </root>
</mxGraphModel>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml)

    return output_path
