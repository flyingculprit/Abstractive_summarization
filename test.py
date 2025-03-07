import google.generativeai as genai

# Configure the API key
genai.configure(api_key="")

# List available models
available_models = genai.list_models()

# Print model names
print("Available Gemini Models:")
for model in available_models:
    print(model.name)
