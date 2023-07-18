from jinja2 import Environment, FileSystemLoader
from database import RSSFeedEntry


def render_html(entries: RSSFeedEntry) -> str:
    """
    Display the entries provided as arguments in HTML format using a Jinja2 template.

    Args:
      entries (RSSFeedEntry): A list of RSSFeedEntry objects
    Returns:
      email_content: a string containing the email content in HTML format
    """

    # Create the Jinja2 environment
    env = Environment(loader=FileSystemLoader('./templates'))

    # Define the template file
    template = env.get_template('email_template.html')

    # Define the data
    rss_feed_title = "My Upwork RSS Feed"

    # Render the template with the data
    email_content = template.render(
        entries=entries, rss_feed_title=rss_feed_title)

    # Return the email content in HTML format
    return email_content
