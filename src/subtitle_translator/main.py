import sys

from deep_translator import GoogleTranslator
from subtitle_parser import SrtParser

if __name__ == "__main__":

    import io
    import textwrap



    # manual
    parser = SrtParser(io.StringIO(textwrap.dedent('''\
        1
        00:00:00,123 --> 00:00:03,456
        Hi there
        
        2
        00:01:04,843 --> 00:01:05,428
        This is an example of a
        subtitle file in SRT format
    ''')))
    parser.parse()

    # file input
    # inp = Path(__file__).parent.parent.parent.absolute() / Path('input/1.srt')
    # with open(inp, 'r', encoding='utf-8') as input_file:
    #     parser = subtitle_parser.SrtParser(input_file)
    #     parser.parse()




    parser.print_warnings()

    texts=[subtitle.text for subtitle in parser.subtitles]
    translated = GoogleTranslator(source='german', target='english').translate_batch(texts)
    sys.exit(1)

    for subtitle in parser.subtitles:
        print(subtitle.text)

    texts = ["hallo welt", "guten morgen"]
    translated = GoogleTranslator(source='german', target='english').translate_batch(texts)
    # translated = GoogleTranslator(source='auto', target='german').translate_file('path/to/file')

    pass
