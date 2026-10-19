"""
content_extra.py - extra traditional-style reflection content that the original database did not contain
(personal growth, wellbeing, relationship tips, work habits) for Moolank/Bhagyank 1-9, plus short mole notes.

Everything here is reflective, general-lifestyle wording. None of it is medical advice or a prediction.
Edit freely - it is plain Python data.
"""

EXTRA = {
    1: dict(
        growth=["Practise listening fully before you decide.", "Share credit openly with people who help you.", "Notice when confidence turns into stubbornness."],
        prompts=["When did I last change my mind because of someone else's advice?", "Which goal am I chasing for myself, and which for approval?", "Who would I like to support more?"],
        love=["Ask your partner's view before you settle a plan.", "Say thank you out loud, not only in action.", "Take turns leading; being equal is also a strength."],
        work="You tend to work best when you own a clear goal and have room to decide how to reach it.",
        skills=["Delegation", "Patient feedback", "Collaborative planning"],
        routine=["Start the day with sunlight and a short walk.", "Keep a fixed time for your most important task.", "Schedule one genuine rest block per week."],
        stress=["Pause before reacting when you feel challenged.", "Write the worry down, then split it into small steps."],
        selfcare=["What would 'enough' look like today?", "Where can I ask for help without feeling smaller?"]),
    2: dict(
        growth=["Voice your needs early instead of absorbing them.", "Make decisions with a deadline so doubt does not linger.", "Remember that kindness and boundaries can live together."],
        prompts=["What do I keep quiet about to keep the peace?", "Which relationship gives me energy, and which drains it?", "What decision have I been postponing?"],
        love=["Tell your partner what you need before it becomes hurt.", "Plan quiet time together without screens.", "Be gentle with moods; check in rather than guess."],
        work="You tend to shine in cooperative, caring or creative settings where listening matters.",
        skills=["Assertive communication", "Decision-making", "Saying no politely"],
        routine=["Keep sleep and meal times regular.", "Spend a little time near water, greenery or calm music.", "Journal for five minutes in the evening."],
        stress=["Limit news and social feeds on tense days.", "Take slow breaths and relax your shoulders on purpose."],
        selfcare=["What am I carrying that belongs to someone else?", "What small comfort can I give myself tonight?"]),
    3: dict(
        growth=["Finish one project before opening the next.", "Turn good advice into daily habits.", "Practise humility when you already know the answer."],
        prompts=["What am I teaching others that I should also practise?", "Which commitments can I let go?", "Where does optimism help me, and where does it avoid reality?"],
        love=["Share your thoughts, but leave space for your partner's.", "Keep promises small and reliable.", "Make time for shared learning or travel."],
        work="You tend to enjoy guiding, teaching and advising roles where wisdom and communication are valued.",
        skills=["Focus and follow-through", "Time management", "Listening without advising"],
        routine=["Walk or stretch daily, even for ten minutes.", "Plan meals instead of improvising them.", "Keep a weekly review of goals."],
        stress=["Avoid over-scheduling; leave gaps in the day.", "Talk to a trusted mentor or friend."],
        selfcare=["Am I giving more than I can sustain?", "What would a slower week look like?"]),
    4: dict(
        growth=["Allow flexibility when plans change.", "Celebrate progress, not only completion.", "Ask for feedback before you are certain you are right."],
        prompts=["Where do rules help me, and where do they trap me?", "What am I building that I truly care about?", "Which risk would I take if I felt prepared?"],
        love=["Show affection in words, not only in practical help.", "Allow spontaneity once in a while.", "Discuss disagreements calmly and early."],
        work="You tend to be strongest in structured, practical, long-term work where careful effort pays off.",
        skills=["Adaptability", "Creative problem-solving", "Team motivation"],
        routine=["Use a simple weekly schedule that includes leisure.", "Spend time outdoors or on a hands-on hobby.", "Wind down at a set hour each night."],
        stress=["Break big worries into a short checklist.", "Relax the need for perfection on at least one task a day."],
        selfcare=["What can be 'good enough' today?", "Who can I trust with part of my load?"]),
    5: dict(
        growth=["Choose one priority and give it steady attention.", "Pause before big spending or sudden decisions.", "Follow through on small commitments."],
        prompts=["What do I run towards, and what do I run from?", "Which habit would I be proud of in a year?", "Where could routine give me more freedom?"],
        love=["Be clear about your intentions and boundaries.", "Create shared adventures and shared plans.", "Listen without hurrying to the next topic."],
        work="You tend to thrive in varied, communication-heavy work with movement, learning and new people.",
        skills=["Consistency", "Financial planning", "Deep focus"],
        routine=["Keep active with something you enjoy.", "Set a regular sleep window, especially on busy weeks.", "Put screens away before bed."],
        stress=["Take short offline breaks during the day.", "Do one thing at a time for ten minutes."],
        selfcare=["What does my body or mind need to slow down?", "What is one thing I can simplify?"]),
    6: dict(
        growth=["Look after your own needs alongside everyone else's.", "Let others solve some of their own problems.", "Keep expectations realistic, in yourself and others."],
        prompts=["Where do I say yes when I mean no?", "What beauty or comfort do I want more of?", "What would I do if no one needed anything from me this week?"],
        love=["Express needs plainly instead of hoping they are noticed.", "Avoid comparing your relationship to others'.", "Make time to enjoy each other, not only to look after the home."],
        work="You tend to do well in roles involving care, design, hospitality, advice or any work with a human touch.",
        skills=["Boundary setting", "Delegating", "Receiving help"],
        routine=["Create a pleasant, tidy space for rest.", "Cook or share a simple meal regularly.", "Keep a daily moment just for yourself."],
        stress=["Notice when caring turns into worrying; take a breath.", "Say 'let me think about it' before agreeing."],
        selfcare=["Who looks after me?", "What would I like to receive this week?"]),
    7: dict(
        growth=["Share thoughts with people you trust.", "Balance time alone with time in company.", "Turn insights into small actions."],
        prompts=["What am I withdrawing from, and why?", "What do I value that I rarely talk about?", "Which question am I really asking?"],
        love=["Tell your partner what you are thinking, even if unfinished.", "Explain when you need quiet so it is not misread.", "Plan simple shared rituals."],
        work="You tend to work well in research, analysis, writing or specialised fields where depth is respected.",
        skills=["Teamwork", "Expressing ideas simply", "Practical follow-through"],
        routine=["Make room for quiet time in nature or meditation.", "Keep regular meals and sleep.", "Limit late-night overthinking with a notebook by the bed."],
        stress=["Move your body to get out of your head.", "Talk to someone before a worry grows."],
        selfcare=["What would help me feel connected today?", "What am I not allowing myself to enjoy?"]),
    8: dict(
        growth=["Rest without guilt; progress is not only effort.", "Offer appreciation as readily as instruction.", "Treat setbacks as slow lessons, not verdicts."],
        prompts=["What does success mean to me, apart from status?", "Where am I too hard on myself?", "Who deserves more of my time than my work does?"],
        love=["Make time for warmth, not only duty.", "Say what you feel before it turns to silence.", "Let your partner share the load."],
        work="You tend to be steady, disciplined and persistent, and often suit long-term responsibilities.",
        skills=["Empathy in leadership", "Work-life balance", "Flexibility"],
        routine=["Keep a regular exercise or stretching habit.", "Schedule days off like appointments.", "Eat unhurried meals away from your desk."],
        stress=["Watch for the thought 'I must do everything alone'.", "Share responsibility with trusted people."],
        selfcare=["What would I do if I had nothing to prove?", "What small joy have I postponed?"]),
    9: dict(
        growth=["Direct your energy before it turns into frustration.", "Think before reacting; a pause is powerful.", "Finish what you start, then rest."],
        prompts=["What cause or goal deserves my energy?", "How do I respond when I feel challenged?", "What am I holding on to that I could forgive?"],
        love=["Speak calmly when you disagree.", "Show care through small, steady gestures.", "Give your partner room to be different."],
        work="You tend to bring courage and drive to demanding, active or service-minded work.",
        skills=["Patience", "Active listening", "Long-term planning"],
        routine=["Use physical activity you enjoy to release tension.", "Keep a calm wind-down routine at night.", "Drink water and keep regular meals when busy."],
        stress=["Count slowly or walk before replying in anger.", "Channel energy into a hobby, sport or creative project."],
        selfcare=["What does my energy want to build, not fight?", "Where can I be gentler this week?"]),
}

MOLE_NOTES = {
    "Forehead": "In Til Shastra a mole on the forehead is traditionally linked with thoughtfulness and ambition.",
    "Eyebrow": "Traditionally, a mole near the eyebrow is associated with an independent and creative nature.",
    "Cheek": "A mole on the cheek is traditionally linked with sociability and a love of company.",
    "Nose": "Traditional readings associate a mole on the nose with initiative and a strong will.",
    "Chin": "Traditionally, a mole on the chin is linked with determination and a practical outlook.",
    "Neck": "Traditional sources associate a mole on the neck with a sensitive, expressive personality.",
    "Hand": "A mole on the hand is traditionally linked with skill, industriousness and resourcefulness.",
    "Other": "Traditional mole reading (Til Shastra) gives meaning by body position; a more specific location would give a more specific note.",
}

CATEGORIES = [
    ("love", "Love & Relationships", "♡", "Communication, compatibility and relationship reflection."),
    ("growth", "Personal Growth", "✦", "Personality themes, strengths and self-reflection prompts."),
    ("career", "Career & Professional Life", "⚑", "Work style, skills to develop and practical career ideas."),
    ("wellbeing", "General Wellbeing", "☾", "Lifestyle reflection, stress management and self-care prompts."),
]
CATEGORY_KEYS = [c[0] for c in CATEGORIES]
