import sys
from pathlib import Path

import subtitle_parser
from deep_translator import GoogleTranslator
from subtitle_parser import SrtParser


def get_subtitles_from_file(inp: str):
    with open(inp, 'r', encoding='utf-8') as input_file:
        parser = subtitle_parser.SrtParser(input_file)
        parser.parse()
        parser.print_warnings()

    return parser.subtitles


def get_subtitles_from_str(inp: str):
    parser = SrtParser(inp)
    parser.parse()
    parser.print_warnings()

    return parser.subtitles


if __name__ == "__main__":

    import io
    import textwrap

    sample_file = Path(__file__).parent.parent.parent.absolute() / Path('input/1.srt')
    sample_str = io.StringIO(textwrap.dedent('''\
        1
        00:00:00,123 --> 00:00:03,456
        Hi there
        
        2
        00:01:04,843 --> 00:01:05,428
        This is an example of a
        subtitle file in SRT format
    '''))

    subtitles = get_subtitles_from_str(sample_str)
    subtitles = get_subtitles_from_file(sample_file)


    texts = [subtitle.text for subtitle in subtitles]

    # translated = GoogleTranslator(source='german', target='english').translate_batch(texts)
    sys.exit(1)

    for subtitle in parser.subtitles:
        print(subtitle.text)

    texts = ["hallo welt", "guten morgen"]
    translated = GoogleTranslator(source='german', target='english').translate_batch(texts)
    # translated = GoogleTranslator(source='auto', target='german').translate_file('path/to/file')

    pass
