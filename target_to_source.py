import os
import xml.etree.ElementTree as ET
import argparse
import sys
from deep_translator import GoogleTranslator
from multiprocessing import Pool
import datetime
import sys

def translate(translator: GoogleTranslator, text: str) -> str:
    return translator.translate(text)

def save_tmx_file(file_path, output_path, tmx_obj, target_language, source_language):
    # Save the TMX object as a file in the output folder
    output_file_path = os.path.join(output_path, f"{os.path.splitext(os.path.basename(file_path))[0]}-{target_language}-{source_language}.tmx")
    ET.ElementTree(tmx_obj).write(output_file_path, encoding="utf-8", xml_declaration=True)

    # Open the output file and insert a newline character after each closing </tu> tag
    with open(output_file_path, "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("</tu>", "</tu>\n").replace("<tuv","\n <tuv").replace("<body>", "<body>\n\n").replace("</tu>","\n</tu>")
        f.seek(0)
        f.write(content)
        f.truncate()

def translate_xml(file_path, source_language, target_language, output_path):
    # Load the xml file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Create a TMX object with the source and target text
    tmx_obj = ET.Element("tmx", version="1.4")
    header = ET.SubElement(tmx_obj, "header", srclang=source_language, datatype="unknown")
    ET.SubElement(header, "prop", type="targetlang").text = target_language
    body = ET.SubElement(tmx_obj, "body")

    # Initialize a list to store the translations
    translator = GoogleTranslator(source=source_language, target=target_language)

    # Loop through each trans-unit element in the xml file
    for trans_unit in root.iter('{urn:oasis:names:tc:xliff:document:1.2}trans-unit'):
        # Get the source text
        source_text = ""
        for child in trans_unit.iter('{urn:oasis:names:tc:xliff:document:1.2}source'):
            if child.text:
                source_text += child.text
            for sub_child in child:
                if sub_child.tail:
                    source_text += sub_child.tail

        # Translate the source text
        if source_text:
            translation = translate(translator=translator, text=source_text)

            tu = ET.SubElement(body, "tu")
            ET.SubElement(tu, "tuv", lang=target_language).append(ET.fromstring(f"<seg>:!! {translation}</seg>"))
            ET.SubElement(tu, "tuv", lang=source_language).append(ET.fromstring(f"<seg>{source_text}</seg>"))

    save_tmx_file(file_path=file_path, output_path=output_path, tmx_obj=tmx_obj, source_language=source_language, target_language=target_language)

if __name__ == '__main__':
    # Define and parse command line arguments
    parser = argparse.ArgumentParser(description='Translate XML files using GoogleTranslator and save as TMX files in the output folder.')
    parser.add_argument('input_folder', type=str, help='path to folder containing XML files to be translated')
    parser.add_argument('source_language', type=str, help='source language of the XML files')
    parser.add_argument('target_language', type=str, help='target language for the translations')
    args = parser.parse_args()

    if len(sys.argv) <3:
        sys.exit()

    # Check if input_folder exists and is a directory
    if not os.path.exists(args.input_folder):
        print(f"Error: {args.input_folder} does not exist.")
        sys.exit()
    if not os.path.isdir(args.input_folder):
        print(f"Error: {args.input_folder} is not a directory.")
        sys.exit()

    # Get a list of all the XML files in the input folder
    data_files = [os.path.join(args.input_folder, f) for f in os.listdir(args.input_folder)]

    # Create the output folder if it doesn't exist
    output_path = os.path.join(args.input_folder, f"output_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Use multiprocessing to translate all the XML files in parallel
    with Pool() as pool:
        # pass source and target languages as arguments to translate_xml function
        pool.starmap(translate_xml, [(f, args.source_language, args.target_language, output_path) for f in data_files])