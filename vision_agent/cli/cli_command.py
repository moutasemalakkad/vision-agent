import os
import sys
import subprocess
import tempfile
from vision_agent.agent import VisionAgent

def execute_code(code, input_image_path, output_image_path):
    """
    Executes the provided code after replacing placeholders with actual paths.

    Parameters:
        code (str): The code to be executed.
        input_image_path (str): The path to the input image.
        output_image_path (str): The path to save the output image.

    Returns:
        str: The standard output of the executed code.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        # Replace placeholders with actual paths
        code_with_paths = code.replace('path/to/your/image.jpg', input_image_path).replace('path/to/output_image.jpg', output_image_path)
        temp_file.write(code_with_paths.encode('utf-8'))
        temp_file_path = temp_file.name

    # Execute the code and capture the output
    result = subprocess.run([sys.executable, temp_file_path], capture_output=True, text=True)
    os.remove(temp_file_path)
    return result.stdout.strip()

def execute_tests(test_code, function_code, input_image_path, output_image_path):
    """
    Executes the provided test code after replacing placeholders with actual paths and combining it with the function code.

    Parameters:
        test_code (str): The test code to be executed.
        function_code (str): The function code to be tested.
        input_image_path (str): The path to the input image.
        output_image_path (str): The path to save the output image.

    Returns:
        tuple: The standard output and standard error of the executed test code.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix="_test.py") as temp_file:
        # Replace placeholders in the test code with actual paths
        modified_test_code = (
            test_code.replace('path/to/actual_input_image.jpg', input_image_path)
            .replace('path/to/output_image.jpg', output_image_path)
        )
        
        # Combine the function code and modified test code
        combined_code = (
            "from vision_agent.tools import load_image, grounding_dino, overlay_bounding_boxes, save_image\n\n" +
            function_code + "\n\n" +
            modified_test_code
        )
        
        temp_file.write(combined_code.encode('utf-8'))
        temp_file_path = temp_file.name

    # Execute the test code and capture the output
    result = subprocess.run([sys.executable, temp_file_path], capture_output=True, text=True)
    os.remove(temp_file_path)
    return result.stdout.strip(), result.stderr.strip()

def main():
    """
    Main function to interact with the Vision-Agent CLI.
    """
    # Check if the OpenAI API key is set
    if "OPENAI_API_KEY" not in os.environ:
        print("Please set the OPENAI_API_KEY environment variable.")
        return

    agent = VisionAgent()
    print("Welcome to the Vision-Agent CLI!")

    while True:
        # Get user input for the task
        user_input = input("What would you like to do? (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break

        # Get and validate the input image path
        input_image_path = input("Enter the input media file path: ")
        if not os.path.isfile(input_image_path):
            print(f"Error: The file '{input_image_path}' does not exist.")
            continue

        # Get the output image path and create the directory if it does not exist
        output_image_path = input("Enter the output media file path: ")
        output_dir = os.path.dirname(output_image_path)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created directory: {output_dir}")

        media_files = [input_image_path]

        # Create a query for the VisionAgent
        query = {"role": "user", "content": user_input, "media": media_files}
        response = agent.chat_with_workflow([query])

        # Extract generated code and test code from the response
        if isinstance(response, dict):
            generated_code = response.get('code', '')
            generated_test = response.get('test', '')
        else:
            generated_code = response
            generated_test = ''

        print("Generated Code:")
        print(generated_code)

        if generated_test:
            print("Generated Test:")
            print(generated_test)

        # Execute and test the generated code
        while True:
            if generated_test:
                # Run the tests and print the output
                test_stdout, test_stderr = execute_tests(generated_test, generated_code, input_image_path, output_image_path)
                print(f"Test stdout:\n{test_stdout}")
                print(f"Test stderr:\n{test_stderr}")

                if test_stderr:
                    # If tests fail, modify the code based on errors
                    print("Tests failed. Modifying code...")
                    query = {"role": "user", "content": f"Modify the code to fix the following test errors:\n{test_stderr}", "media": media_files}
                    response = agent.chat_with_workflow([query])
                    if isinstance(response, dict):
                        generated_code = response.get('code', '')
                        generated_test = response.get('test', '')
                    else:
                        generated_code = response
                        generated_test = ''
                    print("Modified Code:")
                    print(generated_code)
                    print("Modified Test:")
                    print(generated_test)
                else:
                    # If tests pass, break the loop
                    print("All tests passed!")
                    break
            else:
                # If no tests are generated, execute the code directly
                print("No tests generated. Executing code...")
                stdout = execute_code(generated_code, input_image_path, output_image_path)
                print(f"Code execution output:\n{stdout}")
                break

        # Prompt the user to continue or exit
        continue_prompt = input("Do you want to continue? (yes/no): ")
        if continue_prompt.lower() == 'no':
            break

if __name__ == "__main__":
    main()
