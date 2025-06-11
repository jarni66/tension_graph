import json
import networkx as nx
from pyvis.network import Network
import random
import colorsys
from flask import Flask, send_file
import os

app = Flask(__name__)

def generate_graph():
    # Load topics data
    with open('topic_simulation_plot.json', 'r') as file:
        topics_data = json.load(file)

    # Create a dictionary for quick lookup of topic descriptions
    topic_descriptions_map = {item['topic']: item.get('description', 'No description available.') for item in topics_data}

    # Load topic classification data (assuming this file exists)
    # Replace 'topic_classes.json' with your actual file name if different
    try:
        with open('topic_simulation_class.json', 'r') as file:
            topic_classes = json.load(file)
    except FileNotFoundError:
        print("Warning: topic_classes.json not found. Nodes will default to 'other' class color.")
        topic_classes = {"tension_points": [], "decision_points": [], "negotiation_points": []}

    # --- Define Colors for Classes ---
    CLASS_COLORS = {
        "tension_points": "#FF7F7F",  # Light Red
        "decision_points": "#7FBFFF", # Light Blue
        "negotiation_points": "#7FFF7F", # Light Green
        "other": "#D3D3D3"        # Light Grey for uncategorized nodes
    }

    # --- Helper function to determine node color based on class ---
    def get_node_color_by_class(topic_name, classes_data):
        if topic_name in classes_data.get("tension_points", []):
            return CLASS_COLORS["tension_points"], "Tension Point"
        elif topic_name in classes_data.get("decision_points", []):
            return CLASS_COLORS["decision_points"], "Decision Point"
        elif topic_name in classes_data.get("negotiation_points", []):
            return CLASS_COLORS["negotiation_points"], "Negotiation Point"
        else:
            return CLASS_COLORS["other"], "Other Topic"

    # --- Helper function to generate distinct colors (no longer needed for nodes, but kept if user wants to revert) ---
    def generate_colors(n):
        colors = []
        for i in range(n):
            hue = i / n
            saturation = 0.7
            lightness = 0.7
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, saturation, lightness)]
            hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            colors.append(hex_color)
        return colors

    # Collect all unique topics (still useful for ensuring all nodes are processed)
    all_unique_topics = set()
    for item in topics_data:
        all_unique_topics.add(item['topic'])
        for rel_topic in item['relation']:
            all_unique_topics.add(rel_topic)

    # Create a network graph object
    net = Network(height='750px', width='100%', bgcolor='#ffffff', font_color='#333', notebook=True)

    # Configure physics layout for better spacing and visual appeal
    net.barnes_hut(
        gravity=-1000,
        central_gravity=0.1,
        spring_length=300,
        spring_strength=0.01,
        damping=0.5,
        overlap=0.1
    )

    # Add nodes and edges to the graph
    added_nodes = set() # Keep track of nodes already added to avoid duplicates

    for topic_data in topics_data:
        main_topic = topic_data['topic']
        count = topic_data['count']
        relations = topic_data['relation']
        description = topic_descriptions_map.get(main_topic, 'No description available.') # Get description

        # Determine color and class name based on class
        node_color, node_class_name = get_node_color_by_class(main_topic, topic_classes)

        # Add the main topic node
        if main_topic not in added_nodes:
            node_size = max(15, count * 1.8)
            net.add_node(main_topic,
                        label=main_topic,
                        size=node_size,
                        color={'background': node_color, 'border': '#666666'},
                        title=f"Topic: {main_topic}\nClass: {node_class_name}\nCount: {count}\nDescription: {description}",
                        font={'size': 14, 'bold': True},
                        physics=True)
            added_nodes.add(main_topic)

        # Add related topic nodes and edges
        for related_topic in relations:
            # Ensure the related topic node exists
            if related_topic not in added_nodes:
                # Determine color and class name for related topic
                related_node_color, related_node_class_name = get_node_color_by_class(related_topic, topic_classes)
                related_description = topic_descriptions_map.get(related_topic, 'No description available.') # Get description

                related_topic_info = next((item for item in topics_data if item['topic'] == related_topic), None)
                related_count = related_topic_info['count'] if related_topic_info else 10
                node_size_related = max(10, related_count * 1.5)

                net.add_node(related_topic,
                            label=related_topic,
                            size=node_size_related,
                            color={'background': related_node_color, 'border': '#666666'},
                            title=f"Topic: {related_topic}\nClass: {related_node_class_name}\nDescription: {related_description}\n(Related)",
                            font={'size': 12},
                            physics=True)
                added_nodes.add(related_topic)

            # Add an edge between the main topic and the related topic
            net.add_edge(main_topic, related_topic,
                        color='#666666',
                        width=1.5)

    # Add a simple legend to the HTML output
    legend_html = """
    <div style="position: absolute; top: 10px; right: 10px; background: white; padding: 10px; border: 1px solid #ccc; font-family: sans-serif; font-size: 14px;">
        <h3>Legend</h3>
        <p><strong>Node Size:</strong> Represents the 'count' of the topic (larger node = higher count).</p>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: #CCEEFF; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Smaller count example</p>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #CCEEFF; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Larger count example</p>
        </div>
        <p><strong>Node Color by Class:</strong></p>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: #FF7F7F; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Tension Points</p>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: #7FBFFF; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Decision Points</p>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: #7FFF7F; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Negotiation Points</p>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: #D3D3D3; border: 1px solid #888; margin-right: 5px; flex-shrink: 0;"></div>
            <p style="margin: 0;">Other Topics</p>
        </div>
        <p><strong>Edge:</strong> Represents a 'relation' between two topics.</p>
    </div>
    """
    net.save_graph('topic_network_graph.html') 

@app.route('/')
def serve_graph():
    # Generate the graph if it doesn't exist
    if not os.path.exists('network_graph.html'):
        generate_graph()
    return send_file('network_graph.html')

if __name__ == '__main__':
    # Generate the graph on startup
    generate_graph()
    # Run the Flask app
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port) 