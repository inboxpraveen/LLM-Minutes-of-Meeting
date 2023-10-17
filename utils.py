import librosa
import os
from pydub import AudioSegment
import subprocess
from mimetypes import guess_type


def crop_into_segments(
    source_audio_base_path,
    target_path_to_store = os.path.join(os.getcwd(),"temp","temp_cropped_audio"),
    crop_window_duration=(20,40)
):
    """
    Crops a source audio file into segments based on non-muted sections and yields the path of each cropped audio segment.
    
    Parameters:
    - source_audio_base_path (str): Absolute path to the source audio file.
    - target_path_to_store (str): Target directory to store the cropped audio files. Defaults to './temp/temp_cropped_audio'.
    - crop_window_duration (Tuple[int, int]): Tuple representing the minimum and maximum duration of each cropped audio segment in seconds. Defaults to (20, 40).
    
    Yields:
    - str: Absolute path of each cropped audio segment file.
    
    Returns:
    - bool: False if cropping based on silence issue arises or if the source audio path does not exist.
    
    Example:
    for segment in crop_into_segments("/path/to/audio.wav"):
        print("Generated Segment:", segment)
    """
    if os.path.exists(source_audio_base_path):
        if not os.path.exists(target_path_to_store):
            os.makedirs(target_path_to_store)
        
        source_audio_filename = os.path.basename(source_audio_base_path)
        source_filename_without_extension = ".".join(source_audio_filename.split(".")[:-1])

        try:
            loudness_to_detect_silence = AudioSegment.from_file(source_audio_base_path).dBFS
            db_value = int(abs(loudness_to_detect_silence))
        except:
            db_value = -20   
        
        audio_array,sample_rate = librosa.load(source_audio_base_path)
        non_mute_sections = librosa.effects.split(y=audio_array,top_db=db_value)
        del audio_array
        
        time_frame, segment_start_time, difference = [], 0, 0
        
        for each_section in non_mute_sections:
            current_start_time, current_end_time = each_section[0]/sample_rate, each_section[1]/sample_rate
            difference = current_end_time - segment_start_time
            if crop_window_duration[0] <= difference <= crop_window_duration[1]:
                time_frame.append([segment_start_time,(segment_start_time+difference)])
                segment_start_time = current_end_time
                difference = 0
            else:
                if current_end_time == non_mute_sections[len(non_mute_sections)-1][1]/sample_rate and difference < crop_window_duration[0]:
                    time_frame.append([segment_start_time,(segment_start_time+difference)])
        
        if len(time_frame)==0:
            print(f"[WARNING] `{source_audio_base_path}` has cropping based on silence issue.")
            return False
        # all_croped_audios = []
        for each_time_frame in time_frame:
            cropped_audio_filename = os.path.join(target_path_to_store,source_filename_without_extension+"_"+str(round(each_time_frame[0],3))+"_"+str(round(each_time_frame[1],3))+".wav")
            cropping_command = f"ffmpeg -y -i {source_audio_base_path} -ss {round(each_time_frame[0],3)} -to {round(each_time_frame[1],3)} -c copy {cropped_audio_filename} -y"
            p = subprocess.Popen(
                cropping_command.split(), 
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
            (output, err) = p.communicate()
            p_status = p.wait()
            yield cropped_audio_filename
            # all_croped_audios.append(cropped_audio_filename)

        # return all_croped_audios

    else:
        print(f"Audio path is wrong or does not exists: {source_audio_base_path}")
        return False


def convert_to_wav(input_file_path):
    """
    Converts an audio or video file to WAV format using ffmpeg.

    Parameters:
    - input_file_path (str): The path of the input audio or video file.

    Returns:
    - str: The path of the converted WAV file.

    Example:
    convert_to_wav("/path/to/audio_or_video.mp3") returns "/path/to/audio_or_video.wav"
    """

    # Determine the MIME type of the input file
    mime_type, encoding = guess_type(input_file_path)

    if mime_type is None:
        print(f"Could not determine the MIME type of the file: {input_file_path}")
        return ""

    # Extract the main type (either 'audio' or 'video')
    main_type = mime_type.split('/')[0]

    # Initialize basic ffmpeg command
    filename = ".".join(os.path.basename(input_file_path).split(".")[:-1])
    output_file_path = os.path.join(os.path.join(os.getcwd(), "media_storage"), filename + ".wav")

    command = ["ffmpeg", "-i", input_file_path]

    # Add codec and other options based on the main type
    if main_type == 'audio':
        command.extend(["-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"])
    elif main_type == 'video':
        command.extend(["-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"])
    else:
        print(f"Unsupported MIME main type: {main_type}")
        return ""

    command.extend([output_file_path, "-y"])

    try:
        subprocess.run(command, check=True)
        return output_file_path
    except subprocess.CalledProcessError as e:
        print("Error while converting using ffmpeg:", e)
        return ""
