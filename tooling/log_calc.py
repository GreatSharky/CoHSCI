import pandas as pd

# Load your Excel file
df = pd.read_excel("log_results.xlsx")

# Option 1 — filter out rows where Hand classification == 0
df_filtered = df[df['Hand classification'] != 0]

# Calculate mean accuracy from the filtered rows
accuracy_without_class0 = df_filtered['Classifier accuracy'].mean()

print(f"Accuracy excluding class 0: {accuracy_without_class0:.4f}")
print(df_filtered['Classifier accuracy'].count())
# Load your Excel file
df = pd.read_excel("log_results.xlsx")

# Convert the time columns to timedelta objects
time_cols = ['Segmentor time', 'Classifier time', 'Validator time']
for col in time_cols:
    df[col] = pd.to_timedelta(df[col])

# Compute mean durations
mean_times = df[time_cols].mean()
# Count of rows used in each calculation
counts = df[time_cols].count()

print("Average processing times:")
print(mean_times)

print("\nNumber of samples used for each mean:")
print(counts)