"""site_content.py - FAQ text. Answers describe how THIS code actually works (retention days are filled in by app.py)."""

FAQS = [
    ("Is a photo required?",
     "No. Both the face photo and the palm photo are optional. You can get a complete numerology reading with no photo at all."),
    ("Can I get a reading without a photo?",
     "Yes. Moolank, Bhagyank and every selected category are calculated from your name and date of birth using traditional rules, "
     "and are available whether or not you upload anything. You can also upload only a face photo, only a palm photo, or both."),
    ("How are Moolank and Bhagyank calculated?",
     "Moolank (Birth Number) is the day of the month you were born, added digit by digit until one digit remains. "
     "Example: born on the 29th → 2+9 = 11 → 1+1 = 2. Bhagyank (Life Path / Destiny Number) adds every digit of the full date of birth and reduces it the same way. "
     "Example: 16/07/2002 → 1+6+0+7+2+0+0+2 = 18 → 1+8 = 9. Your report shows these steps for your own date."),
    ("How does Gemini AI assist with the reading?",
     "Only when you upload a photo and tick the consent box, that single image (plus a short instruction, and your gender choice for the palm) is sent to Google's Gemini AI, "
     "which writes a speculative, traditional-style reflection. Your name, date of birth and place of birth are not sent. "
     "If Gemini is unavailable, the website says so honestly and your numerology reading still works."),
    ("What happens to uploaded photos?",
     "A photo you upload is re-saved as a JPEG on this website's server (with camera metadata removed) and linked to your reading. "
     "It is kept for up to {days} days, then removed automatically the next time the site runs its clean-up. "
     "You can delete your photos, or your whole reading, at any time using the buttons on your reading pages. "
     "Photos are not shown publicly; only someone who has your private reading link can see them."),
    ("Is the reading a guaranteed prediction?",
     "No. Numerology, palmistry and face reading are traditional practices, not science. Treat the reading as a prompt for reflection, not a forecast. "
     "AI-written parts can be wrong or generic."),
    ("Is the reading a replacement for professional advice?",
     "No. It is not medical, legal, financial or relationship advice. For health, money, legal or relationship decisions, please speak to a qualified professional."),
    ("What does the Vastu Meter do?",
     "You choose the direction of each room in your home. For every room the website looks up the rating and the 1-10 score given for that direction in the Vastu workbook, and shows the average of your scores as an overall meter. "
     "The average is a summary added by this website; the workbook itself contains ratings, not a formula. Nothing you choose is stored."),
    ("Is anything I type into the calculators saved?",
     "No. The Core Numbers Calculator and the Vastu Meter work only for the moment you submit them and do not save your name, dates or room choices. "
     "Only the Personal Reading (with its preview and report) saves a record, so that you can return to it."),
    ("What is free and what is in the complete report?",
     "The preview is free and already includes your two numbers, how they were calculated, a personality overview, strengths, challenges and a short insight for each category you picked. "
     "The complete report adds the full interpretation for each category, practical suggestions, reflection prompts, traditional remedies, compatibility and any photo-based reflection. "
     "{payment_note}"),
    ("How can I contact a human astrologer?",
     "Visit the Astro Buddy website or contact astrologer Dev. Details are on the Contact page and in the footer."),
]
