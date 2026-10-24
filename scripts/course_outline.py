"""Bundled outline parser; derived from local project parser, without import side effects."""
from html.parser import HTMLParser

class Outline(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.nodes = []
        self.active = []
        self.li_stack = []
        self.title = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        capture = (self.elements[-1][1] if self.elements else False) or (tag == 'div' and 'content' in attrs.get('class', '').split())
        self.elements.append((tag, capture))
        if tag == 'li':
            self.li_stack.append('node' in attrs.get('class', '').split())
        if tag == 'li' and 'node' in attrs.get('class', '').split():
            node = {'id': len(self.nodes) + 1, 'depth': len(self.active), 'text_parts': [], 'images': []}
            self.nodes.append(node)
            self.active.append(node)
        if tag == 'img' and self.active:
            self.active[-1]['images'].append({'src': attrs.get('src', ''), 'alt': attrs.get('alt', '')})
        if tag == 'br' and capture and self.active:
            self.active[-1]['text_parts'].append('\n')
        if tag in ('img', 'br', 'meta', 'link', 'hr', 'input', 'wbr'):
            self.elements.pop()

    def handle_endtag(self, tag):
        if tag == 'li' and self.li_stack:
            is_node = self.li_stack.pop()
            if is_node and self.active:
                self.active.pop()
        for i in range(len(self.elements) - 1, -1, -1):
            if self.elements[i][0] == tag:
                del self.elements[i:]
                break

    def handle_data(self, data):
        if self.elements and self.elements[-1][0] == 'title':
            self.title.append(data)
        if self.active and self.elements and self.elements[-1][1]:
            self.active[-1]['text_parts'].append(data)
