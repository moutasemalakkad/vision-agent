import os
import sys
import subprocess
import tempfile
from vision_agent.agent import VisionAgent

def execute_code(code, image_path):
    # Create a temporary file to save the code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        code_with_path = code.replace('path/to/your/image.jpg', image_path)
        temp_file.write(code_with_path.encode('utf-8'))
        temp_file_path = temp_file.name

    # Execute the temporary file and capture the output
    result = subprocess.run([sys.executable, temp_file_path], capture_output=True, text=True)

    # Print the stdout
    print(result.stdout.strip())

    # Clean up the temporary file
    os.remove(temp_file_path)

    return result.stdout.strip()

def main():
    if "OPENAI_API_KEY" not in os.environ:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    agent = VisionAgent()
    print("Welcome to the Vision-Agent CLI!")

    while True:
        user_input = input("What would you like to do? (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break

        media_files_input = input("Enter the media file paths (comma-separated, leave blank if none): ")
        media_files = [media.strip() for media in media_files_input.split(',') if media.strip()]

        # Prepare the input for VisionAgent
        if media_files:
            query = {"role": "user", "content": user_input, "media": media_files}
            response = agent.chat_with_workflow([query])
        else:
            response = agent(user_input)

        # Extract the code from the response
        if isinstance(response, dict):
            generated_code = response.get('code', '')
        else:
            generated_code = response

        # Modify the generated code to print only the caption
        if 'return' in generated_code:
            generated_code += f"\nif __name__ == '__main__':\n    print(describe_image('{media_files[0]}'))"

        print("Generated Code:")
        print(generated_code)

        # Ask if the user wants to execute the code
        execute = input("Do you want to execute this code? (yes/no): ")
        if execute.lower() == 'yes' and generated_code:
            stdout = execute_code(generated_code, media_files[0])
            print(f"stdout= {stdout}")

        # Ask if the user wants to continue
        continue_prompt = input("Do you want to continue? (yes/no): ")
        if continue_prompt.lower() == 'no':
            break

if __name__ == "__main__":
    main()
