from bs4 import BeautifulSoup
import requests


def replace_mask_logo(file_path: str, logo_svg: str):
    """
        Replace the <g mask="url(#mask1_5005_58782)">...</g> element
        with a custom logo SVG snippet.

        Args:
            file_path: Path to the HTML file
            logo_svg:   String containing your replacement SVG markup
        """

    # Load HTML
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Step 1: Remove/replace mask branding ---
    masked_element = soup.find('g', {'mask': 'url(#mask1_5005_58782)'})
    if masked_element:
        # For now we just remove, later you can replace with your own <image> or <g>
        masked_element.decompose()

    # --- Step 2: Inline Google Fonts ---
    for link_tag in soup.find_all('link', href=True, rel=lambda v: v and "stylesheet" in v):
        href = link_tag['href']
        if "fonts.googleapis.com" in href:
            try:
                css = requests.get(href, timeout=10).text
                style_tag = soup.new_tag("style")
                style_tag.string = css
                link_tag.replace_with(style_tag)
            except Exception as e:
                print(e)

    # Save updated HTML
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))