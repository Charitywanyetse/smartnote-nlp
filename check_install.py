print("Checking installed packages...")
print("-" * 30)

try:
    import flask
    print("✅ Flask installed")
except:
    print("❌ Flask missing")

try:
    import spacy
    print("✅ spaCy installed")
except:
    print("❌ spaCy missing")

try:
    import textblob
    print("✅ TextBlob installed")
except:
    print("❌ TextBlob missing")

try:
    import dateparser
    print("✅ dateparser installed")
except:
    print("❌ dateparser missing")

try:
    import pandas
    print("✅ pandas installed")
except:
    print("❌ pandas missing")

print("-" * 30)
print("All good! Ready to build the NLP project.")