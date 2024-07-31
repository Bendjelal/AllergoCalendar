import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import cm
from matplotlib.lines import Line2D
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

def read_dates_from_input(dates, intervals):
    parsed_dates = []
    parsed_intervals = []
    for date_info in dates:
        date, description, category = date_info
        parsed_dates.append((pd.to_datetime(date, dayfirst=True), description, category))

    for interval_info in intervals:
        start, end, description = interval_info
        parsed_intervals.append((pd.to_datetime(start, dayfirst=True), pd.to_datetime(end, dayfirst=True), description))

    return parsed_dates, parsed_intervals

def adjust_text_positions(text_positions, min_distance=0.1):
    adjusted_positions = []
    for pos in text_positions:
        new_pos = pos
        while any(abs(new_pos - adj_pos) < min_distance for adj_pos in adjusted_positions):
            new_pos += min_distance
        adjusted_positions.append(new_pos)
    return adjusted_positions

def generate_timeline(dates, intervals, output_file='timeline.png'):
    plt.rcParams['font.family'] = 'Arial'
    fig, ax = plt.subplots(figsize=(10, 6))
    all_dates = [date for date, _, _ in dates] + [date for interval in intervals for date in interval[:2]]
    all_dates = [pd.to_datetime(date) for date in all_dates]
    min_date = min(all_dates).to_pydatetime()
    max_date = max(all_dates).to_pydatetime()
    ax.set_xlim(min_date, max_date)
    ax.set_ylim(-len(intervals) - 2, 3)
    ax.margins(x=0.05)
    date_text_positions = []
    for date, description, category in dates:
        if category == 'Contact':
            ax.plot(date.to_pydatetime(), 0, 'ro', markersize=10)
        elif category == 'Traitement':
            ax.plot(date.to_pydatetime(), 0, marker='*', color='orange', markersize=20)
        date_text_positions.append((date.to_pydatetime(), 0.2, f'{date.strftime("%d-%m-%Y")}\n{description}'))
    date_text_positions = sorted(date_text_positions, key=lambda x: x[0])
    adjusted_date_text_positions = adjust_text_positions([pos[1] for pos in date_text_positions], min_distance=0.6)
    for (date, _, text), new_y in zip(date_text_positions, adjusted_date_text_positions):
        ax.text(date, new_y, text, ha='center', fontsize=12)
        line = Line2D([date, date], [0, new_y - 0.1], color='black', linewidth=0.5)
        ax.add_line(line)
    interval_groups = defaultdict(list)
    for start, end, description in intervals:
        interval_groups[description].append((start, end))
    cmap = cm.get_cmap('cividis', len(interval_groups))
    colors = {description: cmap(i) for i, description in enumerate(interval_groups)}
    interval_text_positions = []
    descriptions = []
    for i, (description, intervals) in enumerate(interval_groups.items()):
        y_position = -(i + 1)
        color = colors[description]
        for start, end in intervals:
            rect = Rectangle((start.to_pydatetime(), y_position), end.to_pydatetime() - start.to_pydatetime(), 0.8, color=color, alpha=0.6)
            ax.add_patch(rect)
        text_x = min([start.to_pydatetime() for start, end in intervals]) + (max([end.to_pydatetime() for start, end in intervals]) - min([start.to_pydatetime() for start, end in intervals])) / 2
        interval_text_positions.append((text_x, y_position + 0.4, description))
    interval_text_positions = sorted(interval_text_positions, key=lambda x: x[0])
    adjusted_interval_text_positions = adjust_text_positions([pos[0].timestamp() for pos in interval_text_positions], min_distance=0.1)
    adjusted_interval_text_positions_datetime = [datetime.fromtimestamp(pos) for pos in adjusted_interval_text_positions]
    for (text_x, text_y, description), new_text_x in zip(interval_text_positions, adjusted_interval_text_positions_datetime):
        ax.text(new_text_x, text_y, description, ha='center', va='center', fontsize=12, color='black')
    ax.yaxis.set_visible(False)
    ax.xaxis.set_ticks_position('none')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, which='both', axis='x', linestyle='--', linewidth=0.5)
    ax.xaxis.grid(False)
    plt.savefig(output_file, bbox_inches='tight', dpi=300)
    plt.close()
    image = Image.open(output_file)
    return image

if 'events' not in st.session_state:
    st.session_state.events = list(range(4))

st.title("Interactive Timeline Creator")
st.write("Enter your dates and intervals below:")

date_entries = []
interval_entries = []

for i in range(len(st.session_state.events)):
    st.write(f"### Event {i+1}")
    cols = st.columns(5)
    with cols[0]:
        event_type = st.selectbox("Type", ["Date ponctuelle", "Plage de dates"], key=f"type_{i}")
    with cols[1]:
        date_1 = st.text_input("Date 1 (JJ-MM-AAAA)", key=f"date1_{i}", value=datetime.today().strftime("%d-%m-%Y"))
    with cols[2]:
        date_2 = st.text_input("Date 2 (JJ-MM-AAAA)", key=f"date2_{i}", value=datetime.today().strftime("%d-%m-%Y")) if event_type == "Plage de dates" else None
    with cols[3]:
        category = st.selectbox("Catégorie", ["Contact", "Traitement"], key=f"cat_{i}") if event_type == "Date ponctuelle" else None
    with cols[4]:
        description = st.text_input("Légende", key=f"desc_{i}")

    if event_type == "Date ponctuelle":
        date_entries.append((date_1, description, category))
    else:
        interval_entries.append((date_1, date_2, description))

if st.button("Ajouter une ligne"):
    st.session_state.events.append(len(st.session_state.events))

if st.button("Générer la frise chronologique"):
    dates, intervals = read_dates_from_input(date_entries, interval_entries)
    timeline_image = generate_timeline(dates, intervals)
    st.image(timeline_image, caption="Timeline")
