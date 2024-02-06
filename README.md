# Transcription-Application

The core functionality of [Ton-Texter](https://ton-texter.de) is to transcribe audio and video files. Therefore we use models based on OpenAIs [Whisper](https://github.com/openai/whisper). Additionally we perform a speaker diarization with [Pyannote](https://huggingface.co/pyannote). Although this implementation came with some problems at first, that needed to be resolved, it is now a key component of Ton-Texters offering and a unique selling point compared to other solutions that are solely based on Whisper.

This repository represents the Python application that we execute on an Amazon EC2 Instance to run the transcription. Theoretically this application can also be run locally on a CUDA capable device. 

## Participants

| Name            | Abbreviation |
| --------------- | ------------ |
| Hannes Koksch   | hk058        |
| Nikolas Schaber | ns144        |
| Torben Ziegler  | tz023        |



## How to run the application locally

> Prerequisites: Your machine has a CUDA capable GPU and the necessary drivers already installed. Python does also have to be installed for the installation script to work.

To run the application locally on your machine you will have to clone this repository and execute the `install.bat` file. This file should install all the necessary libraries.  

Within our cloud infrastructure the application gets the necessary secrets to access our api, the S3 bucket, etc. from AWS Secrets Manager. If you want to use it locally you have to change the loading of the secret in the `main.py` file. Instead of:

```python
from get_secret import get_secret
# Get Secret
secret = get_secret()
#with open('env.json') as secret_file:
#   secret = json.load(secret_file)
```

Change the `main.py` file to this:

```python
#from get_secret import get_secret
# Get Secret
#secret = get_secret()
with open('env.json') as secret_file:
   secret = json.load(secret_file)
```

As you might have notice already this does require you to setup an `env.json` file with the secret values. The JSON file should look like this:

```json
{
    "API_URL": "",
    "TRANSCRIPTION_SERVICE_API_KEY": "",
    "MODIFY_URL": "",
    "BUCKET_NAME": "",
    "SECRET_KEY": "",
    "ACCESS_KEY": "",
    "HUG_TOKEN": ""
}
```

`API_URL` : The application expects an URL to get tasks from. Transcripts are returned from our API in the following format:

```json
{"transcripts":[{"id":"","fileName":"Test123-6c70ad05-42a3-4fb5-b16e-c53f7db2b500","fileExtension":".wav","fileNameWithExt":"Test123-6c70ad05-42a3-4fb5-b16e-c53f7db2b500.wav","displayFilename":"Test123.wav","preview":"SPEAKER_00:  And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country. \n","status":"SUCCESS","createdAt":"2024-02-01T10:04:14.318Z","updatedAt":"2024-02-01T10:05:08.804Z","userId":"ab63cb3a-98db-488b-9750-0133f49f6cfe"},...]}
```

`TRANSCRIPTION_SERVICE_API_KEY ` :  The API key for our API

`MODIFY_URL`: The endpoint to update the status of a transcript

`BUCKET_NAME`: The name of the AWS S3 bucket to save the transcript files to

`SECRET_KEY`: Secret key of the S3 bucket

`ACCESS_KEY`: Access key of the S3 bucket

`HUG_TOKEN`: Huggingface Token to get the Pyannote model for speaker diarization



After you have setup this file you should be ready to run the application. Remember to activate the Python virtual environment and execute the `main.py` file:

```bash
python main.py
```



## Usage

If you just want to test our already deployed application, proceed as follows:

1. Visit the [Ton-Texter](https://ton-texter.de) application in your browser.

2. Create an account with invitation key "cct2024".

3. Go to "Dashboard".

4. Click on the "Datei hochladen" button to select and upload your audio file.

5. Wait for the transcription process to complete.

6. Download your transcriptions in DOCX, SRT, and TXT formats.

## Related repositories

- [Cloud-Transcription-Service](https://github.com/ns144/Cloud-Transcription-Service)
- [Ton-Texter](https://github.com/hanneskoksch/ton-texter)