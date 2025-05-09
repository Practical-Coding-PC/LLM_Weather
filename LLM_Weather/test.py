import google.generativeai as genai

genai.configure(api_key="AIzaSyC-BtbEw2RuUQvSxIY5UehKgTqIff3AN8A")

models = genai.list_models()
for m in models:
    print(m.name)