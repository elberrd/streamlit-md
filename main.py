import streamlit as st
import requests
import html2text
from bs4 import BeautifulSoup
import base64
from datetime import datetime, timedelta
import re

# Classe para gerenciar cada projeto
class Project:
    def __init__(self, name):
        self.name = name
        self.urls = ""
        self.selected_tags = ['article']
        self.markdown_output = ""
        self.file_name = 'md-export.md'
        self.ignore_links = True
        self.ignore_images = True
        self.log = []
        self.urls_tags = {}

def remove_duplicates(urls):
    return list(dict.fromkeys(urls))

def html_to_markdown(url, tags, ignore_links, ignore_images):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        content = ""
        for tag in tags:
            for element in soup.find_all(tag):
                content += str(element)

        if not content:
            return "No specified tags found in the HTML."

        markdown_converter = html2text.HTML2Text()
        markdown_converter.ignore_links = ignore_links
        markdown_converter.ignore_images = ignore_images
        markdown_text = markdown_converter.handle(content)

        return markdown_text
    except requests.RequestException as e:
        return f"An error occurred: {e}"

def process_urls(urls_tags, project):
    combined_markdown = ""
    for url, tags in urls_tags.items():
        combined_markdown += html_to_markdown(url, tags, project.ignore_links, project.ignore_images) + "\n\n"
    return combined_markdown

def download_markdown(markdown_text, filename):
    b64 = base64.b64encode(markdown_text.encode()).decode()
    href = f'<a href="data:file/markdown;base64,{b64}" download="{filename}" target="_blank">Click here to download your markdown file</a>'
    return href

def clear_project_data(project):
    project.urls = ""
    project.selected_tags = ['article']
    project.markdown_output = ""
    project.log = []
    project.urls_tags = {}

def main():
    st.sidebar.title("Projects")
    session_state = st.session_state

    if 'projects' not in session_state:
        session_state.projects = [Project("Project 1")]

    if st.sidebar.button("Add New Project"):
        new_project_name = f"Project {len(session_state.projects) + 1}"
        session_state.projects.append(Project(new_project_name))
        session_state.current_project = session_state.projects[-1]

    project_names = [project.name for project in session_state.projects]
    selected_project_name = st.sidebar.selectbox("Select a Project", project_names, index=0)
    session_state.current_project = next((project for project in session_state.projects if project.name == selected_project_name), None)

    st.title(session_state.current_project.name)
    html_tags = ['article', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'section', 'header', 'footer', 'ul', 'ol', 'li']
    selected_tags = st.multiselect("Select HTML tags to convert:", html_tags, default=session_state.current_project.selected_tags)
    urls_input = st.text_area("Enter URLs (one per line):", session_state.current_project.urls, height=150)
    ignore_links = st.checkbox("Ignore Links", value=session_state.current_project.ignore_links)
    ignore_images = st.checkbox("Ignore Images", value=session_state.current_project.ignore_images)

    if st.button("Process Links"):
        urls = re.findall(r'https?://[^\s)\]]+', urls_input)
        unique_urls = remove_duplicates(urls)
        session_state.current_project.urls_tags = {url: selected_tags for url in unique_urls}
        for url in unique_urls:
            st.text(url)
            session_state.current_project.urls_tags[url] = st.multiselect(f"Select tags for {url}:", html_tags, default=selected_tags)

    if st.button("Process Content"):
        session_state.current_project.markdown_output = process_urls(session_state.current_project.urls_tags, session_state.current_project)
        st.markdown("## Markdown Output")
        st.text_area("Markdown", session_state.current_project.markdown_output, height=400)

        session_state.current_project.file_name = st.text_input("Enter the name of the file to save:", session_state.current_project.file_name)
        if session_state.current_project.file_name:
            download_link = download_markdown(session_state.current_project.markdown_output, session_state.current_project.file_name)
            st.markdown(download_link, unsafe_allow_html=True)

    with st.expander("Project Config"):
        new_name = st.text_input("Rename Project", value=session_state.current_project.name)
        if st.button("Update Name"):
            session_state.current_project.name = new_name
            project_names[project_names.index(selected_project_name)] = new_name
            st.experimental_rerun()

    with st.expander("Logs"):
        for entry in session_state.current_project.log:
            st.text(f"{entry['time']} - {entry['url']} - {entry['status']}")

if __name__ == "__main__":
    main()
