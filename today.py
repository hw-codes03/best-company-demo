from datetime import date

today = date.today()
print(f"Today's date is {today:%A, %B %d, %Y} ({today.isoformat()})")
