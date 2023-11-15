import streamlit as st
import requests
import html2text
from bs4 import BeautifulSoup
import base64
from datetime import datetime

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

def remove_duplicates_and_log(urls, project):
    unique_urls = []
    for url in urls:
        if url not in unique_urls:
            unique_urls.append(url)
        else:
            log_entry = {
                "url": url, 
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "status": "Removed Duplicate"
            }
            project.log.append(log_entry)
    return unique_urls

def html_to_markdown(url, tags, ignore_links, ignore_images, project):
    log_entry = {"url": url, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        content = ""
        for tag in tags:
            for element in soup.find_all(tag):
                content += str(element)

        if not content:
            raise ValueError("No specified tags found in the HTML.")

        markdown_converter = html2text.HTML2Text()
        markdown_converter.ignore_links = ignore_links
        markdown_converter.ignore_images = ignore_images
        markdown_text = markdown_converter.handle(content)

        log_entry["status"] = "OK"
        project.log.append(log_entry)
        return markdown_text
    except Exception as e:
        log_entry["status"] = f"Error: {e}"
        project.log.append(log_entry)
        return ""

def process_urls(urls, tags, ignore_links, ignore_images, progress_bar, project):
    combined_markdown = []
    total_urls = len(urls)
    for idx, url in enumerate(urls):
        markdown_text = html_to_markdown(url, tags, ignore_links, ignore_images, project)
        combined_markdown.append(markdown_text)
        progress_bar.progress((idx + 1) / total_urls)
    return "\n\n---\n\n".join(combined_markdown)

def download_markdown(markdown_text, filename):
    b64 = base64.b64encode(markdown_text.encode()).decode()
    href = f'<a href="data:file/markdown;base64,{b64}" download="{filename}" target="_blank">Click here to download your markdown file</a>'
    return href

def clear_project_data(project):
    project.urls = ""
    project.selected_tags = ['article']
    project.markdown_output = ""
    project.log = []

# Função principal do Streamlit
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
    selected_project_name = st.sidebar.selectbox("Select a Project", project_names, index=len(session_state.projects) - 1)
    session_state.current_project = next((project for project in session_state.projects if project.name == selected_project_name), None)

    st.title(session_state.current_project.name)
    tab1, tab2, tab3 = st.tabs(["Download", "Config", "Log"])

    with tab1:
        html_tags = ['article', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'section', 'header', 'footer', 'ul', 'ol', 'li']
        session_state.current_project.selected_tags = st.multiselect("Select HTML tags to convert:", html_tags, default=session_state.current_project.selected_tags)
        session_state.current_project.urls = st.text_area("Enter URLs (one per line):", session_state.current_project.urls, height=150)
        session_state.current_project.ignore_links = st.checkbox("Ignore Links", value=session_state.current_project.ignore_links)
        session_state.current_project.ignore_images = st.checkbox("Ignore Images", value=session_state.current_project.ignore_images)

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button('Process URLs'):
                urls = session_state.current_project.urls.split("\n")
                unique_urls = remove_duplicates_and_log(urls, session_state.current_project)
                if unique_urls and session_state.current_project.selected_tags:
                    progress_bar = st.progress(0)
                    session_state.current_project.markdown_output = process_urls(unique_urls, session_state.current_project.selected_tags, session_state.current_project.ignore_links, session_state.current_project.ignore_images, progress_bar, session_state.current_project)
                    st.markdown("## Markdown Output")
                    st.text_area("Markdown", session_state.current_project.markdown_output, height=400)
                    session_state.current_project.file_name = st.text_input("Enter the name of the file to save:", session_state.current_project.file_name)
                    if session_state.current_project.file_name:
                        download_link = download_markdown(session_state.current_project.markdown_output, session_state.current_project.file_name)
                        st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.markdown("## Markdown Output")
                st.text_area("Markdown", session_state.current_project.markdown_output, height=400)

        with col2:
            if st.button('Clear All'):
                session_state.clear_clicked = True

        if 'clear_clicked' not in session_state:
            session_state.clear_clicked = False

        if session_state.clear_clicked:
            clear_project_data(session_state.current_project)
            session_state.clear_clicked = False

    with tab2:
        new_name = st.text_input("Rename Project", value=session_state.current_project.name)
        if st.button("Update Name"):
            session_state.current_project.name = new_name
            st.experimental_rerun()

        if st.button("Delete Project"):
            session_state.projects = [project for project in session_state.projects if project != session_state.current_project]
            session_state.current_project = session_state.projects[0] if session_state.projects else None
            st.experimental_rerun()

    with tab3:
        if session_state.current_project.log:
            for entry in session_state.current_project.log:
                st.text(f"{entry['time']} - {entry['url']} - {entry['status']}")
        else:
            st.text("No log entries.")

if __name__ == "__main__":
    main()
