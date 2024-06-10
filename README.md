# LLM-Minutes-of-Meeting

### Table of Contents

| Sr. No. | Topic                                 | Link                    |
| ------- | ------------------------------------- | ----------------------- |
| 0.      | Introduction and "Why" of the project | [Link will come here]() |
| 1.      | Setup and Installation                | [Link will come here]() |
| 2.      | Features                              | [Another Link]()        |
| 3.      | Demo and Application Screenshots      | [Another Link]()        |
| 4.      | Approach and Implementation*          | [Another Link]()        |
| 5.      | Recent Updates and Future Directions  | [Another Link]()        |
| 6.      | Contributions                         | [Another Link]()        |
| 7.      | Issues/Troubleshooting                | [Another Link]()        |

## 0. Introduction and "Why" of the project

<img src="static/images/github/mom.png" alt="Meeting Minutes AI Image" />

The primary objective of this project is to showcase NLP & LLM's capability to quickly summarise long meetings and help you and your organisation automate the task of delegating Minutes of Meeting(MoM) emails. It uses a high level 2 step approach where step 1 corresponds to conversion of any audio/video file into a text conversation. Step 2 utilises text produced by step 1 and generate Minutes of meeting and detailed summary notes. These minutes of meeting will be editable piece of text. Once you finalise the MoM, you can use it further as per your requirement. 

The long term objective for this repository is also to develop a real time python web-application which can attend meetings for you and also provide you MoM at the end of the meeting. Taking baby steps and trying to get to long-term by starting a short term objective.

------

**<u>For your Information</u>: I am working on fine-tuning custom LLMs and development. Please be patient while the whole project is completely stable. I will add training & inference code once completed. Do :star: this repository if you need to know latest updates.** :smile: **Appreciate your time.** 

------



## 1. Setup and Installation

Before proceeding, ensure you have the following installed:

- Ubuntu 22.04 or latest.
- Python (v3.10 or higher)
- A virtual environment tool like `virtualenv` or `venv`.

Let's begin installation steps now.

1. **Clone the GitHub Repository**

   Open your terminal or command prompt and navigate to the directory where you want to clone the repository. Then run:

   ```bash
   git clone https://github.com/inboxpraveen/LLM-Minutes-of-Meeting
   cd LLM-Minutes-of-Meeting
   ```

2. **Install Requirements**

   It's a good practice to create a virtual environment before installing dependencies to avoid potential conflicts with other Python projects. If you're using `virtualenv`, you can set up a new environment as follows:

   ```bash
   ## Create a python virtual environment and activate it.
   # Install the required packages after activating:
   pip install -r requirements.txt
   
   ## After this, let's install Llama-Cpp-Python binding which will be used to interact with LLMs. 
   
   ## Run the following line if you are using it on a CPU.
   pip install llama-cpp-python
   
   ## Run the following line if you are using GPU (T4, A100, A10, or H100), or any Nvidia Cuda based GPU Drivers.
   CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
   
   ## If you are on Mac or any other GPU types, you can refer the following links and setup the Llama-Cpp-Python
   
   https://llama-cpp-python.readthedocs.io/en/stable/#installation-configuration
   
   https://llama-cpp-python.readthedocs.io/en/stable/install/macos/
   ```

3. **Setup RabbitMQ & Celery Background Job Processing**

   Use the following link to setup RabbitMQ on your machine. Follow the directions till ***step 5*** and save your `admin-username` & `password`.

   [Setup RabbitMQ on Ubuntu 22.04](https://www.cherryservers.com/blog/how-to-install-and-start-using-rabbitmq-on-ubuntu-22-04)

   Once you have successfully setup RabbitMQ, then setup redis-server and celery. Use the following command to setup and install them.

   ```bash
   sudo apt-get update -y
   ## Try with apt-get. If it does not install, then run with apt. 
   sudo apt-get install redis-server -y 
   ## If the above does not work, try this:
   sudo apt install redis-server -y
   ```

4. **Run Application and Parallel Run Celery Task**

First, start the Flask application:

```bash
cd /path/to/project/
```

and then open app.py file inside you code editor and modify the following line. 

```python
Line 18:     broker='amqp://<user>:<password>$@localhost:5672//'

## Update <user> with "your-admin-username".
## Update <password> with "your-admin-password"
## Eg: broker='amqp://admin:hello_world$@localhost:5672//'

### IMPORTANT NOTE: If your password contains '@' symbol, you will need to convert it because it is the default delimiter in broker settings. Example if your password has @ symbol inside it would be. 
## broker='amqp://admin:hello%40world$@localhost:5672//'  -- where the original password was "hello@world", we represent it as 'hello%40world'
```

After you have updated the file, you will run the `setup.py` file to setup directories and download of models. If you want to change the configurations of which models you wish to use, you can change them appropriately based on your infrastructure size and system capacity. The following table shows which models we support currently in this project but we will be adding new LLMs support as we see them fit and open-source.

<u>**Speech Models Supported**</u>

| Model Name                      | Model Size | Memory Required (RAM or vRAM) |
| ------------------------------- | ---------- | ----------------------------- |
| distil-whisper/distil-large-v3  | 3.1 GB     | 4 GB                          |
| distil-whisper/distil-large-v2  | 3.1 GB     | 4 GB                          |
| distil-whisper/distil-medium.en | 1.6 GB     | 2 GB                          |
| distil-whisper/distil-small.en  | 680 MB     | 900 MB                        |
| openai/whisper-large-v3         | 6.2 GB     | 7.5 GB                        |
| openai/whisper-large-v2         | 6.2 GB     | 7.5 GB                        |
| openai/whisper-large-v1         | 6.2 GB     | 7.5 GB                        |
| openai/whisper-medium           | 3.2 GB     | 4.5 GB                        |
| openai/whisper-small (default)  | 980 MB     | 1.7 GB                        |

**<u>LLMs Supported</u>**

| Model Name                                         | Model Size   | Memory Required |
| -------------------------------------------------- | ------------ | --------------- |
| QuantFactory/Phi-3-mini-4k-instruct-GGUF (default) | 1 GB - 8 GB  | 2 GB - 14 GB    |
| QuantFactory/Phi-3-mini-128k-instruct-GGUF         | 1 GB - 8 GB  | 2.5 GB - 16 GB  |
| bartowski/Phi-3-medium-128k-instruct-GGUF          | 3 GB - 14 GB | 6 GB - 18 GB    |

You will need to modify the `global_varibables.py` file with the model name you choose and then run `setup.py` file which will automatically down the models you choose.

```python
Line 32: DEFAULT_SPEECH_MODEL = "openai/whisper-small"
...
Line 46: DEFAULT_SUMMARY_MODEL = ("QuantFactory/Phi-3-mini-4k-instruct-GGUF", "Phi-3-mini-4k-instruct.Q5_0.gguf")


### After update the above lines as per your need, run the setup.py
python setup.py
```

In a new terminal window (ensure your virtual environment is activated here as well), start the App and Celery worker:

```bash
python app.py # ensure your environment is activated

# and then in new terminal, run the following.
celery -A app.celery worker --loglevel=info -f celery.logs
```

1. **Upload Recording to Form**

   Open your web browser and navigate to the Flask application's URL (usually `http://127.0.0.1:5000`). Use the interface to upload your meeting recording.

2. **Get Latest Status and Wait for It to Complete**

   After uploading the recording, you can check the status of the processing. This could be implemented as a status page or a progress bar in your application. Wait until the processing is complete.

3. **See the Final Processed Minutes of Meeting (MoM)**

   Once the processing is complete, the application should display the final minutes of the meeting. You can view, edit (if the feature is available), and save the MoM for your reference.

## 2. Features: :sparkles: 

- Effortlessly convert audio and video files to accurate text transcripts: These can also be used to summarise, generate action items, understanding work-flows, and resource planning. 

- Keyword highlighting and topic tagging for quick reference: Extracting topics and finding relevant contents to skip through meetings and listen to only specific topics which is of your interest.

- Export minutes in various formats, including PDF and plain text: Allows you to export meeting transcripts, summaries, topic & keywords, action items, etc into documents which can be utilized in project planning and management frameworks. Also eliminates your need to manually write and generate templates.

- User-friendly interface for easy customization and integration: Easy to tweak which ever open-source or closed source model you want to choose. 



## Approach and Implementation: :bulb: 

### Overview

The core functionality revolves around processing meeting recordings submitted via the home page of the web application. Once a recording is submitted, a background task is initiated using Celery, which performs two primary operations: speech-to-text conversion and generating minutes of the meeting from the converted text.

### Implementation

The flowchart you've shared outlines a detailed process for handling and processing media files, particularly focusing on audio and video inputs to generate transcriptions and summaries. Let’s break down each step and describe the high-level solutions involved in this workflow:

##### 1. **Upload Media File**
   - **Media Types**: Supports mp3, wav, mp4 files.
   - **Action**: Users upload their media files to the system.

##### 2. **Async Loop for Real-Time Notification**
   - **Purpose**: To keep users informed about the status of their upload and processing.
   - **Implementation**: Use an asynchronous notification API to send real-time updates to the user.

##### 3. **Read Uploaded File**
   - **Action**: The system reads the uploaded file to determine the type and content.

##### 4. **Branching for Audio and Video**
   - **Audio**:
     - **Convert to 16 kHz**: Standardize audio sample rate for consistent processing.
     - **Transcribe**: Convert audio speech to text.
   - **Video**:
     - **Extract Audio and Frames (1 Frame/Second)**: Separate audio track and video frames for processing.
     - **Short Summary Per Frame**: Generate a brief summary for each extracted frame.

##### 5. **Join All Short Summary and Create Main Transcription (for Video)**
   - **Action**: Combine all short summaries into a single comprehensive transcription of the video content.

##### 6. **Split if Number of Token > 4000**
   - **Purpose**: Handle limitations of the processing language model which might have a maximum token input limit.
   - **Implementation**: If the transcription exceeds the token limit, split the content into manageable parts.

##### 7. **Recursive MoM Language Model**
   - **Generate Video MoM (Minutes of Meeting)**: If the input is a video, generate a detailed summary or minutes from the transcription.
   - **Recursive Processing**: For longer content, recursively summarize to condense the information effectively.

##### 8. **Generated Summary and MoM**
   - **Action**: Produce a final summary and minutes of the meeting document based on the transcribed and processed text.

##### 9. **Merge Both MoM and Get New MoM**
   - **Purpose**: Combine summaries from different chunks (if split previously) into a final comprehensive document.

##### 10. **Notification of Process Completion**
   - **Integration with Notification API**: Inform the user that the processing is complete and provide access to the generated summaries or MoM documents.

### Flow Diagram

<img src="static/images/github/flow.png" alt="Data Preparation Loop Flow Diagram" />



## Technical Stack: :computer: 

- **Back-end**: Python, Flask
- **Asynchronous Task Queue**: Redis, Celery
- **Speech-to-Text**: Whisper, Faster-Whisper, Distil-Whisper
- **LLM for Text Processing**: Phi3, Gemma 2, Llama 3
- **Frontend**: HTML, CSS, JavaScript



## Use Cases and Applications: :white_check_mark: 

1. **Corporate Meetings**: Enhances productivity by providing quick and accurate minutes for various corporate gatherings, board meetings, and team discussions.
2. **Educational Institutions**: Useful for lecturers and students to transcribe and summarize lectures, seminars, and group discussions.
3. **Legal and Medical Fields**: Helps in accurately documenting legal proceedings, interviews, and patient consultations.
4. **Accessibility**: Assists individuals with disabilities, especially those who have difficulties in note-taking, by providing an automated way to capture and summarize spoken content.
5. **Event Coverage**: Useful for journalists and event organizers to transcribe speeches, presentations, and panel discussions, aiding in report creation and event documentation.



## Future Scope and Enhancements: :crystal_ball: 

- Integration with video conferencing tools for direct recording capture.
- Multi-language support for speech-to-text conversion.
- Enhanced summarization features tailored to specific meeting types (e.g., technical, business strategy).
- Real-time transcription and summarization capabilities.
- User customization options for formatting the minutes.



## Sample Screenshots of Application:

1. Home Screen.

<img src="static/images/app/1.png" alt="Screenshot 1" />

2. New Minutes of Meeting Dialogue

<img src="static/images/app/2.png" alt="Screenshot 2" />

3. Upload Video/Audio File.

<img src="static/images/app/3.png" alt="Screenshot 3" />

4. Notification Center - Started Processing

<img src="static/images/app/4.png" alt="Screenshot 4" />

5. Notification Center - In Prgress Real Time Updates

<img src="static/images/app/5.png" alt="Screenshot 5" />

6. Notification Center - Completed Processing

<img src="static/images/app/6.png" alt="Screenshot 6" />

7. Final Minutes of Meeting Page

<img src="static/images/app/7.png" alt="Screenshot 7" />

8. Notification Center - Multiple File Status

<img src="static/images/app/8.png" alt="Screenshot 8" />

9. Notification Center - Multiple File Status

<img src="static/images/app/9.png" alt="Screenshot 9" />

10. Notification Center - Multiple File Status

<img src="static/images/app/10.png" alt="Screenshot 10" />


## Running the Tool Locally: :slot_machine: 

### Prerequisites

Before proceeding, ensure you have the following installed:

- Ubuntu 22.04 or latest.
- Python (v3.10 or higher)
- A virtual environment tool like `virtualenv` or `venv`.

### Installation and Setup:



## Troubleshooting: :bug: 

- Ensure all environment variables required by the application and Celery are correctly set.
- Check for any error messages in the Flask and Celery terminal outputs.
- Make sure the versions of Python and the packages in `requirements.txt` are compatible.



## Phase 2 - Real-Time Transcriptions: :next_track_button: 
In Phase 2 of our project, we plan to enable real-time meeting transcription. Join us in shaping the future of efficient and collaborative meetings!



## Stay Updated: 

🔍 Follow me for updates on Phase 2 development and other enhancements to make your meetings even more productive.



## Contributions Welcome: 

👩‍💻 Encouraging contributions from the community to make this tool a game-changer for meetings everywhere. Contribute your ideas and expertise to help us achieve real-time transcription!
