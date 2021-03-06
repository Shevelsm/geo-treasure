import json
import logging
import os
from subprocess import check_output

from branca.element import Element
from folium import Icon, Popup, Html
import matplotlib.pyplot as plt

from geotreasure.model import db, Point


def save_point_to_db(title, source, url, lat, long, info):
    url_exists = Point.query.filter(Point.url == url).count()
    title_exists = Point.query.filter(Point.title == title).count()
    logging.debug(f"count this point {url_exists or title_exists}")
    if not (url_exists or title_exists):
        point = Point(
            title=title, source=source, url=url, lat=lat, long=long, info=info,
        )
        db.session.add(point)
        db.session.commit()


def create_popup_and_icon(query_list, host_url):
    # generate icon
    number_of_points = len(query_list)

    if number_of_points < 5:
        icon_color = "blue"
    elif number_of_points < 10:
        icon_color = "green"
    elif number_of_points < 20:
        icon_color = "yellow"
    elif number_of_points < 30:
        icon_color = "orange"
    else:
        icon_color = "red"

    # generate popup
    sources = [row[3] for row in query_list]
    alter, auto, geo = (
        sources.count("altertravel"),
        sources.count("autotravel"),
        sources.count("geocaching"),
    )

    text = Html(
        '<img src="{}popup.png?geo={}&alter={}&auto={}" alt="popup_pie">'.format(
            host_url, geo, alter, auto
        ),
        script=True,
    )

    return Popup(html=text), Icon(color=icon_color, icon="info-sign")


def create_pie_chart_figure(geo_count, alter_count, auto_count):
    LABELS = ("geocaching", "altertravel", "autotravel")
    sizes = [geo_count, alter_count, auto_count]
    COLORS = ["lightgreen", "gold", "lightskyblue"]
    fig, ax = plt.subplots(figsize=(1.5, 0.8))
    ax.pie(sizes, colors=COLORS, shadow=True, startangle=140)
    ax.legend(
        labels=LABELS,
        fontsize="xx-small",
        loc="center right",
        bbox_to_anchor=(2.25, 0.5),
    )
    plt.subplots_adjust(left=0.0, bottom=0.1, right=0.45)
    return fig


def add_on_click_handler_to_marker(folium_map, marker, cluster_id, host_url):
    my_js = """
            {0}.on('click', function(e) {{
                parent.postMessage({1}, "{2}");
            }});
            """.format(
        marker.get_name(), cluster_id, host_url
    )
    e = Element(my_js)
    html = folium_map.get_root()
    html.script.get_root().render()
    html.script._children[e.get_name()] = e


def markers_generator():
    """ range - searching radius for places """
    path_to_file = os.path.join("geotreasure", "data", "ready50dots.json")
    with open(path_to_file, "r", encoding="utf-8") as file:
        markers_data = json.loads(file.read())
    return markers_data


def get_server_url():
    ips = check_output(["hostname", "--all-ip-addresses"])
    return "http://{}/".format(str(ips.split()[0])[2:-1])
