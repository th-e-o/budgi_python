import streamlit.components.v1 as components
import os

_RELEASE = False  # Set to False for development

if not _RELEASE:
    _univer_sheet_component = components.declare_component(
        "univer_sheet_component",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _univer_sheet_component = components.declare_component(
        "univer_sheet_component", path=build_dir
    )


def excel_viewer(initial_data=None, update_command=None, height=600, key=None, default=None):
    """
    Streamlit component to render an Excel-like sheet using Univer.

    :param workbook_data: A dict representing the workbook in Univer's format.
    :param key: Streamlit key for the component.
    :return: The updated workbook data as a dict if changes were made.
    """
    component_value = _univer_sheet_component(
        initial_data=initial_data,
        update_command=update_command,
        height=height,
        key=key,
        default=default
    )
    return component_value
