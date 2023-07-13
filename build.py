"""
Building the presentation using the reveal js .

command to build html page.
    - python3 build.py
        or 
    - make slide
"""

from subprocess import run
import os
import base64
from bs4 import BeautifulSoup
from requests import get
from inquirer import Text, List, prompt, themes

SOURCE_FILE_NAME = ""

DEPS = [
    "npm init -y",
    "npm i --save asciidoctor @asciidoctor/reveal.js",
]


class RevealJsException(Exception):
    pass


"""
Creating the Project template folder.
"""
INITIAL_MESSAGE = "creating the revealjs presentation \n NOTE:\n \t* audio and video content if project needs create either audio and video \n\n \t\t(or)\n\n\t\t figures may contains all the resources file's.... \n\n\n"


def get_audiodata(url: str):
    sub_type = url.split(".")[-1]
    content = get_base64_data(url)
    if sub_type in audio_formats:
        print("Audio File Present", sub_type, url)
        return f"data:audio/{sub_type};base64,{content}"


def get_videodata(url: str):
    sub_type = url.split(".")[-1]
    content = get_base64_data(url)
    if sub_type in video_formats:
        print("Video File Present", sub_type, url)
        return f"data:video/{sub_type};base64,{content}"


def create_template():
    prompt_list = [
        Text(
            "slide_name",
            "project name for reveal js presentation \n example: slide.adoc",
            default="slide.adoc",
            show_default="slide.adoc",
        ),
        List(
            "audio",
            "create the audio directory for audio files ",
            choices=["yes", "no"],
            default="no",
        ),
        List(
            "video",
            message="create the video directory for video files",
            choices=["yes", "no"],
            default="no",
        ),
        List(
            "figures",
            message="create a figures directory for all the images , video ,audio file's",
            default="yes",
            choices=["yes", "no"],
        ),
    ]
    answers = prompt(
        prompt_list,
        theme=themes.BlueComposure(),
    )
    for question in answers.keys():
        print(question)
        if question == "slide_name":
            if (
                len(
                    list(
                        filter(
                            lambda file_ext: file_ext in str(answers.get(question)),
                            [".md", ".adoc", ".asciidoc"],
                        )
                    )
                )
                >= 1
            ):
                create_file(file_path=answers.get(question))
        else:
            for key, value in answers.items():
                if value == "yes":
                    os.makedirs(key, exist_ok=True)

            # print(
            #     *map(
            #         lambda args: (
            #             not os.path.exists(args.get("yes")) and create_dir(**args)
            #         ),
            #         filter(
            #             None,
            #             map(
            #                 lambda key: {answers.get(key): key}
            #                 if answers.get(key) == "yes"
            #                 else None,
            #                 answers.keys(),
            #             ),
            #         ),
            #     )
            # )
            return


def install_script(command):
    return run(command, shell=True, stderr=open(os.devnull))


def install_deps():
    """
    Installation for building the reveal js presentation.
    """
    if not os.path.exists("node_modules"):
        [*map(install_script, DEPS)]
    else:
        return


video_formats = ["mp4", "avi", "mkv", "mov", "wmv"]
audio_formats = ["mp3", "wav", "aac", "ogg", "flac"]


def run_npx_with_asciidoc(source_filename="slides.adoc"):
    if not source_filename:
        raise RevealJsException("Provide the RST FILE PATH ....")
    if not os.path.exists(source_filename):
        raise RevealJsException("RST FILE PATH NOT YET EXIST....")

    if SOURCE_FILE_NAME := source_filename.strip().split(".")[0]:
        command = (
            f"npx asciidoctor-revealjs -o  {SOURCE_FILE_NAME}.html {source_filename}"
        )
        response = run(f"{command}", stderr=open(os.devnull), shell=True)
        if response.returncode != 0:
            raise RevealJsException(
                "Something went's wrong when runing building the slides adoc file into html file."
            )
        else:
            print("Successfully Builded html")
    else:
        raise RevealJsException("FILE NAME IS NOT PRESEN ...")


def get_imagedata(url: str):
    if url.__contains__("http") or url.__contains__("https"):
        data = get(url, stream=True)
        print(data)
        return base64.b64encode(data.content).decode()
    else:
        return get_base64_data(url)


def extract_paths(html_file):
    with open(html_file, "r") as file:
        soup = BeautifulSoup(file, "html.parser")
        script_tags = soup.find_all("script")
        link_tags = soup.find_all("link")
        img_tag = soup.find_all("img")
        section_tag = soup.find_all("section")
        audio_tags = soup.find_all("audio")
        video_tags = soup.find_all("video")

        paths = []

        # Extract paths from <script> tags
        for script in script_tags:
            if "src" in script.attrs:
                path = script["src"]
                if "node_modules/" in path:
                    empty_script_tag = soup.new_tag("script")
                    empty_script_tag.string = open(path).read()
                    empty_script_tag.attrs = {"crossorgin": ""}
                    script.replace_with(empty_script_tag)
                    paths.append(os.path.join(os.path.dirname(html_file), path))

        for link in link_tags:
            if "href" in link.attrs:
                path = link["href"]
                if "node_modules/" in path:
                    empty_link_tag = soup.new_tag("style")
                    empty_link_tag.attrs = {"type": "text/css"}
                    empty_link_tag.string = open(path).read()
                    link.replace_with(empty_link_tag)
                    paths.append(os.path.join(os.path.dirname(html_file), path))

        for img in img_tag:
            if "src" in img.attrs:
                path = img.get("src")
                image_type = path.split(".")[-1]
                if ("figures/" or "images/") in path:
                    empty_img_tag = soup.new_tag("img")
                    empty_img_tag.attrs = {
                        **img.attrs,
                        "src": f"data:image/{image_type};base64,{get_base64_data(path)}",
                    }
                    img.replace_with(empty_img_tag)

        for section in section_tag:
            video_path = ""
            image_path = ""
            if "data-background-image" in section.attrs:
                image_path = section.get("data-background-image")
                if image_path:
                    image_type = image_path.strip().split(".")[-1]
                    img_data = get_imagedata(image_path)
                    empty_section_tag = soup.new_tag("section")
                    empty_section_tag.attrs = {
                        **section.attrs,
                        "data-background-image": f"data:image/{image_type};base64,{img_data}",
                    }
                    section.replace_with(empty_section_tag)
                    return
            else:
                video_path = section.get("data-background-video")
                if video_path and not (
                    "http" in str(video_path) or "https" in str(video_path)
                ):
                    video_type = video_path.strip().split(".")[-1]
                    img_data = get_imagedata(video_path)
                    empty_section_tag = soup.new_tag("section")
                    empty_section_tag.attrs = {
                        **section.attrs,
                        "data-background-video": f"data:video/{video_type};base64,{img_data}",
                    }
                    section.replace_with(empty_section_tag)

        for audio in audio_tags:
            try:
                if "src" in audio.attrs:
                    path = audio.get("src")
                    if ("audio" or "music" or "figures") in path:
                        empty_audio_tag = soup.new_tag("audio")
                        empty_audio_tag.attrs = {
                            **audio.attrs,
                            "src": get_audiodata(path),
                        }

                        audio.replace_with(empty_audio_tag)

            except Exception as e:
                print(
                    f"""
                            {'*'*30}
                            \t \t
                            {e.args}
                            \t \t
                            {'*'*30}
                    """
                )
            for video in video_tags:
                try:
                    if "src" in video.attrs:
                        path = video.get("src")
                        if ("video" or "figures" or "music") in path:
                            empty_video_tag = soup.new_tag("video")
                            empty_video_tag.attrs = {
                                **video.attrs,
                                "src": get_videodata(path),
                            }

                            video.replace_with(empty_audio_tag)

                except Exception as e:
                    print(
                        f"""
                                {'*'*30}
                                {e.args}
                                {'*'*30}
                        """
                    )

        modified_html = str(soup)
        delete_file(html_file)
        create_file(modified_html, html_file)
        """
        For the Future use ....
        """
        return paths


def delete_file(filename):
    print("Deleting Html file ...")
    os.remove(filename)


def create_file(content="", file_path=""):
    with open(file_path, "w") as modified_file:
        modified_file.write(content)


def get_base64_data(file_name):
    with open(file_name, "rb") as fp:
        return base64.b64encode(fp.read()).decode()


"""
FIXME:
    when appending the content with jinja templates or using the string format wont works
"""


def render_template(paths):
    from collections import ChainMap

    data_with_path = []
    for path in paths:
        data_with_path.append({path: open(path, "r").read()})

    data = dict(ChainMap(*data_with_path))
    return data


def build(filename=None):
    install_deps()
    run_npx_with_asciidoc(filename)
    _ = extract_paths(filename.split(".")[0] + ".html")


def get_rstfilename():
    import sys

    return filter(lambda filename: (".adoc" or ".asciidoc") in filename, sys.argv)


if __name__ == "__main__":
    """
    creating the index.html file from your asciidoc file
    """
    for file in get_rstfilename():
        print(INITIAL_MESSAGE)
        # create_template()
        print(file)
        build(file)
