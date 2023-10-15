import librosa
import os
from pydub import AudioSegment
import datetime
import subprocess

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
        all_croped_audios = []
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
            # yield cropped_audio_filename
            all_croped_audios.append(cropped_audio_filename)

        return all_croped_audios

    else:
        print(f"Audio path is wrong or does not exists: {source_audio_base_path}")
        return False


def generate_excel_name():
    """
    Generates an Excel filename based on the current date and time.
    
    Returns:
    - str: Filename for the Excel file in the format 'YYYY_MM_HH.xlsx'.
    
    Example:
    generate_excel_name() returns '2023_10_14.xlsx'
    """
    now = datetime.datetime.now()
    return f"{now.year}_{now.month}_{now.hour}.xlsx"