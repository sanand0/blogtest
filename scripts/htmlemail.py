#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-frontmatter>=1.0.0",
#     "markdown>=3.5.0",
#     "premailer>=3.10.0",
#     "pygments>=2.17.0",
#     "typer>=0.12.0",
#     "google-auth>=2.0.0",
#     "google-auth-oauthlib>=1.0.0",
#     "google-auth-httplib2>=0.2.0",
#     "google-api-python-client>=2.0.0",
# ]
# ///
"""Convert markdown blog posts to email-friendly HTML."""

import base64
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import frontmatter
import markdown
import typer
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from premailer import transform
from pygments.formatters import HtmlFormatter

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def resolve_links(html: str, base_url: str) -> str:
    """Resolve relative and absolute links to full URLs.

    Args:
        html: HTML content
        base_url: Base URL for resolving links (e.g., https://www.s-anand.net/blog/post-slug/)

    Returns:
        HTML with resolved links
    """
    from urllib.parse import urljoin

    # Replace href attributes
    def replace_href(match):
        url = match.group(1)
        resolved = urljoin(base_url, url)
        return f'href="{resolved}"'

    # Replace src attributes
    def replace_src(match):
        url = match.group(1)
        resolved = urljoin(base_url, url)
        return f'src="{resolved}"'

    html = re.sub(r'href="([^"]+)"', replace_href, html)
    html = re.sub(r'src="([^"]+)"', replace_src, html)

    return html


def replace_youtube_embeds(html: str) -> str:
    """Replace YouTube iframe embeds with clickable thumbnail images.

    Converts iframes to a format like:
    <a href="https://youtu.be/VIDEO_ID">
        <img src="https://i.ytimg.com/vi_webp/VIDEO_ID/sddefault.webp" alt="YouTube video">
    </a>
    """
    # Match YouTube iframe embeds
    youtube_pattern = r'<iframe[^>]*src="(?:https?:)?//(?:www\.)?youtube\.com/embed/([^"?]+)[^"]*"[^>]*>.*?</iframe>'

    def replace_iframe(match):
        video_id = match.group(1)
        return (
            f'<a href="https://youtu.be/{video_id}">'
            f'<img src="https://i.ytimg.com/vi_webp/{video_id}/sddefault.webp" '
            f'alt="YouTube video" style="max-width: 100%; height: auto;">'
            f"</a>"
        )

    return re.sub(youtube_pattern, replace_iframe, html, flags=re.IGNORECASE | re.DOTALL)


def markdown_to_email_html(markdown_file: Path) -> tuple[str, str]:
    """Convert a markdown file to email-friendly HTML.

    Args:
        markdown_file: Path to the markdown file

    Returns:
        Tuple of (email subject, email HTML body with inlined CSS)
    """
    # Parse frontmatter and content
    post = frontmatter.load(markdown_file)
    content = re.sub(r"\\[ \t]*(\r?\n)", r"\1", post.content)

    # Convert markdown to HTML with extensions for tables, code blocks, etc.
    html_content = markdown.markdown(
        content,
        extensions=[
            "extra",  # Includes tables, fenced code blocks, etc.
            "codehilite",  # Syntax highlighting (requires Pygments)
            "nl2br",  # Newline to <br>
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
            }
        },
    )

    # Replace YouTube embeds with image links
    html_content = replace_youtube_embeds(html_content)

    # Extract slug from markdown file path
    # Expected path: posts/YYYY/slug.md
    slug = markdown_file.stem  # Get filename without extension
    base_url = f"https://www.s-anand.net/blog/{slug}/"

    # Resolve relative/absolute links
    html_content = resolve_links(html_content, base_url)

    # Append home page link at the end
    # home_link = '<hr><p style="margin-top: 2em;"><a href="https://www.s-anand.net/">From: s-anand.net</a></p>'
    # html_content = html_content + home_link

    # Generate Pygments CSS for syntax highlighting
    formatter = HtmlFormatter(style="default")
    pygments_css = formatter.get_style_defs(".highlight")

    # Wrap in a basic HTML structure with simple, human-friendly styling
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{post.get("title", "Blog Post")}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                max-width: 600px;
                background-color: #ffffff;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                font-weight: 600;
            }}
            h1 {{ font-size: 2em; }}
            h2 {{ font-size: 1.5em; }}
            h3 {{ font-size: 1.25em; }}
            p {{ margin-bottom: 1em; }}
            a {{ color: #0366d6; text-decoration: underline; }}
            img {{ max-width: 100%; height: auto; margin: 1em 0; }}
            code {{
                padding: 0.2em 0.4em;
                font-size: 90%;
                background-color: #f5f5f5;
                border-radius: 3px;
                font-family: ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'DejaVu Sans Mono', monospace;
            }}
            pre {{
                padding: 1em;
                overflow: auto;
                background-color: #f5f5f5;
                border-radius: 3px;
                margin: 1em 0;
            }}
            pre code {{
                padding: 0;
                background-color: transparent;
            }}
            .highlight {{
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 3px;
                margin: 1em 0;
            }}
            .highlight pre {{
                background-color: transparent;
                padding: 0;
                margin: 0;
            }}
            /* Pygments syntax highlighting styles */
            {pygments_css}
            table {{
                border-collapse: collapse;
                margin: 1em 0;
            }}
            table th, table td {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            table th {{
                font-weight: 600;
                background-color: #f5f5f5;
            }}
            blockquote {{
                padding-left: 1em;
                color: #666;
                border-left: 3px solid #ddd;
                margin: 1em 0;
            }}
            hr {{
                border: 0;
                border-top: 1px solid #ddd;
                margin: 2em 0;
            }}
            ul, ol {{ padding-left: 2em; margin: 1em 0; }}
            li {{ margin-bottom: 0.5em; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Use premailer to inline CSS for email compatibility
    email_html = transform(html_template)

    subject = post.get("title", "Blog Post")
    return subject, email_html


def get_credentials():
    """Authenticate and return credentials for Google APIs."""
    creds = None
    token_path = Path("token.json")
    credentials_path = Path("credentials.json")

    if not credentials_path.exists():
        typer.echo("Error: credentials.json not found in current directory", err=True)
        raise typer.Exit(1)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return creds


def send_email(gmail_service, people_service, to: str, subject: str, html_body: str):
    """Send an email via Gmail API.

    Args:
        gmail_service: Gmail API service object
        people_service: People API service object
        to: Recipient email address
        subject: Email subject
        html_body: HTML email body
    """
    # Get sender's email address from Gmail profile
    profile = gmail_service.users().getProfile(userId="me").execute()
    email_address = profile["emailAddress"]

    # Get sender's display name from People API
    person = people_service.people().get(resourceName="people/me", personFields="names").execute()

    # Extract display name (fallback to email if not available)
    display_name = email_address
    if "names" in person and person["names"]:
        display_name = person["names"][0].get("displayName", email_address)

    message = MIMEMultipart("alternative")
    message["To"] = to
    message["From"] = f'"{display_name}" <{email_address}>'
    message["Subject"] = subject

    # Attach HTML body
    html_part = MIMEText(html_body, "html")
    message.attach(html_part)

    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    # Send the message
    gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()


def main(
    markdown_file: Path = typer.Argument(..., help="Markdown file path to convert"),
    email: str = typer.Option(None, "--email", help="Send email via Gmail API"),
):
    """Convert markdown blog posts to email-friendly HTML.

    The title from the frontmatter will be used as the email subject (not included in body).

    Examples:
        # Print HTML to stdout
        uv run scripts/htmlemail.py ./posts/2026/open-sandals.md

        # Send email via Gmail
        uv run scripts/htmlemail.py ./posts/2026/open-sandals.md --email user@example.com
    """
    if not markdown_file.exists():
        typer.echo(f"Error: File not found: {markdown_file}", err=True)
        raise typer.Exit(1)

    # Convert to HTML
    subject, html = markdown_to_email_html(markdown_file)

    if email:
        # Send via Gmail API
        typer.echo(f"Sending email to {email}...")
        creds = get_credentials()
        gmail_service = build("gmail", "v1", credentials=creds)
        people_service = build("people", "v1", credentials=creds)
        send_email(gmail_service, people_service, email, subject, html)
        typer.echo(f"✓ Email sent to {email} with subject: {subject}")
    else:
        # Print to stdout
        typer.echo(html)


if __name__ == "__main__":
    typer.run(main)
