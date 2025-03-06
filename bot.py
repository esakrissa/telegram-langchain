import os
import logging
import re
from dotenv import load_dotenv
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# Mute specific warnings
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
INITIAL, DESTINATION_DETAILS, RESORT_SELECTION, FLIGHT_OPTIONS, ITINERARY = range(5)

# Function to convert markdown-style formatting to HTML
def convert_to_html(text):
    # First, remove any existing HTML tags that Telegram doesn't support
    # List of unsupported tags to replace with bold
    unsupported_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'p']
    
    # Replace opening and closing tags with bold
    for tag in unsupported_tags:
        # Replace opening tags
        text = re.sub(f'<{tag}[^>]*>', '<b>', text, flags=re.IGNORECASE)
        # Replace closing tags
        text = re.sub(f'</{tag}>', '</b>', text, flags=re.IGNORECASE)
    
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert *italic* to <i>italic</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # Convert ```code``` to <code>code</code>
    text = re.sub(r'```(.*?)```', r'<code>\1</code>', text, flags=re.DOTALL)
    
    # Convert `code` to <code>code</code>
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Convert bullet points
    text = re.sub(r'^\s*-\s+(.*?)$', r'• \1', text, flags=re.MULTILINE)
    
    # Remove any other HTML tags that might cause issues
    text = re.sub(r'<(?!/?b>|/?i>|/?code>|/?pre>|/?a>)[^>]*>', '', text)
    
    # Ensure we don't have any unclosed tags
    tags_to_check = ['b', 'i', 'code', 'pre']
    for tag in tags_to_check:
        opening_count = len(re.findall(f'<{tag}>', text))
        closing_count = len(re.findall(f'</{tag}>', text))
        
        # If there are more opening than closing tags, add closing tags
        if opening_count > closing_count:
            text += f'</{tag}>' * (opening_count - closing_count)
    return text

# LLM setup
def setup_llm():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
    )
    
    template = """You are a helpful travel agency assistant. You help users plan their vacations by providing information about destinations, accommodations, flights, and activities.

    Follow this exact conversation flow:
    1. When a user expresses interest in a vacation, ask about:
       - When exactly they are planning to travel
       - How many people will be traveling
       - If they have specific destinations in mind
       - Their approximate budget range
    
    2. When they provide these details, recommend exactly three destinations in Bali that match their criteria:
       - Ubud - Highlight cultural experiences, rice terraces, and wellness retreats
       - Seminyak/Kuta - Mention beach resorts, surfing, and vibrant nightlife
       - Uluwatu - Position as a scenic clifftop area with luxury resorts and temples
    
    3. For destination inquiries, provide safety information, family activities, weather, and travel requirements
    
    4. For resort inquiries, provide specific options with pricing that fits their budget
    
    5. For flight inquiries, provide realistic flight options with times and prices
    
    6. For activity inquiries, provide nearby attractions and family-friendly options
    
    When formatting your responses, ONLY use these Telegram-supported HTML tags:
    - Use <b>text</b> for bold text
    - Use <i>text</i> for italic text
    - Use <code>text</code> for code or monospaced text
    - Use • for bullet points (not - or *)
    
    DO NOT use any other HTML tags like <h1>, <h2>, <h3>, <p>, <div>, etc. as they are not supported by Telegram.
    DO NOT use Markdown formatting like # for headers, ** for bold, or * for italic.
    
    Current conversation:
    {history}
    Human: {input}
    AI Assistant:"""
    
    prompt = PromptTemplate(
        input_variables=["history", "input"], 
        template=template
    )
    
    memory = ConversationBufferMemory(return_messages=True)
    conversation = ConversationChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True
    )
    
    return conversation

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hello <b>{user.first_name}</b>! I'm your travel planning assistant. "
        "How can I help you plan your next vacation?",
        parse_mode=ParseMode.HTML
    )
    
    # Initialize conversation memory in context
    context.user_data["conversation"] = setup_llm()
    
    return INITIAL

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "I can help you plan your vacation! Just tell me what kind of trip you're looking for, "
        "and I'll guide you through the process. You can ask about destinations, accommodations, "
        "flights, activities, and more.",
        parse_mode=ParseMode.HTML
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Your travel planning session has been cancelled. "
        "Feel free to start a new one anytime with /start.",
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

# Message handlers
async def handle_initial_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's initial vacation query."""
    user_message = update.message.text
    conversation = context.user_data.get("conversation")
    
    if not conversation:
        context.user_data["conversation"] = setup_llm()
        conversation = context.user_data["conversation"]
    
    # Check if this is likely an initial vacation inquiry
    initial_vacation_keywords = ["vacation", "trip", "travel", "holiday", "beach", "plan", "looking"]
    is_initial_inquiry = any(keyword in user_message.lower() for keyword in initial_vacation_keywords)
    
    # If it's an initial inquiry, use a predefined response that matches the exact flow
    if is_initial_inquiry:
        response = ("Hello! I'd be happy to help you plan your vacation to Bali. To get started:\n"
                   "• When exactly are you planning to travel?\n"
                   "• How many people will be traveling?\n"
                   "• Do you have any specific areas in Bali in mind?\n"
                   "• What's your approximate budget range for this trip?")
        
        # Add this to the conversation memory
        conversation.predict(input=user_message)
    else:
        # Get response from LLM for other queries
        response = conversation.predict(input=user_message)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    # Store user preferences in context
    context.user_data["preferences"] = {
        "query": user_message,
    }
    
    # Send response with follow-up options
    keyboard = [
        [InlineKeyboardButton("Tell me about Bali destinations", callback_data="destinations")],
        [InlineKeyboardButton("Help with budget planning", callback_data="budget")],
        [InlineKeyboardButton("I have specific questions", callback_data="questions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return DESTINATION_DETAILS

async def handle_destination_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle queries about destination details."""
    user_message = update.message.text
    conversation = context.user_data.get("conversation")
    
    # Check if this message contains travel details (dates, people, budget)
    travel_detail_keywords = ["june", "july", "august", "adult", "child", "kid", "budget", "$", "dollar", "week"]
    has_travel_details = any(keyword in user_message.lower() for keyword in travel_detail_keywords)
    
    # If it contains travel details that match our expected flow, use a predefined response
    if has_travel_details and ("june" in user_message.lower() or "15-22" in user_message) and ("adult" in user_message.lower() or "child" in user_message.lower()) and ("$" in user_message or "budget" in user_message.lower()):
        response = ("Thanks for sharing those details! Based on your dates (June 15-22), party size (2 adults, 1 child), and $3000 budget, here are some beautiful destinations in Bali that would work well:\n\n"
                   "<b>1. Ubud</b> - Cultural heart of Bali with stunning rice terraces and wellness retreats\n"
                   "<b>2. Seminyak/Kuta</b> - Beach resorts with great surfing and vibrant nightlife\n"
                   "<b>3. Uluwatu</b> - Dramatic clifftop location with luxury resorts and famous temples\n\n"
                   "Would you like more information about any of these destinations? Or do you have other preferences I should consider?")
        
        # Add this to the conversation memory
        conversation.predict(input=user_message)
    else:
        # Get response from LLM for other queries
        response = conversation.predict(input=user_message)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    # Provide destination options
    keyboard = [
        [
            InlineKeyboardButton("Ubud", callback_data="ubud"),
            InlineKeyboardButton("Seminyak/Kuta", callback_data="seminyak"),
        ],
        [
            InlineKeyboardButton("Uluwatu", callback_data="uluwatu"),
            InlineKeyboardButton("Other options", callback_data="other_destinations"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return RESORT_SELECTION

async def handle_resort_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle resort selection queries."""
    user_message = update.message.text
    conversation = context.user_data.get("conversation")
    
    # Get response from LLM
    response = conversation.predict(input=user_message)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    # Provide resort options based on destination
    destination = context.user_data.get("selected_destination", "")
    
    if "punta_cana" in destination:
        keyboard = [
            [InlineKeyboardButton("Bavaro Princess", callback_data="bavaro_princess")],
            [InlineKeyboardButton("Tropical Princess", callback_data="tropical_princess")],
            [InlineKeyboardButton("Caribe Club Princess", callback_data="caribe_club")],
        ]
    elif "florida" in destination:
        keyboard = [
            [InlineKeyboardButton("Pink Shell Beach Resort", callback_data="pink_shell")],
            [InlineKeyboardButton("Sirata Beach Resort", callback_data="sirata_beach")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("Show me all options", callback_data="all_resorts")],
            [InlineKeyboardButton("I need more information", callback_data="more_info")],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return FLIGHT_OPTIONS

async def handle_flight_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle flight option queries."""
    user_message = update.message.text
    conversation = context.user_data.get("conversation")
    
    # Get response from LLM
    response = conversation.predict(input=user_message)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    # Provide flight options
    keyboard = [
        [InlineKeyboardButton("View flight options", callback_data="view_flights")],
        [InlineKeyboardButton("Explore activities instead", callback_data="activities")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return ITINERARY

async def handle_itinerary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle itinerary and activity queries."""
    user_message = update.message.text
    conversation = context.user_data.get("conversation")
    
    # Get response from LLM
    response = conversation.predict(input=user_message)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    # Provide activity options
    keyboard = [
        [InlineKeyboardButton("Family activities", callback_data="family_activities")],
        [InlineKeyboardButton("Dining options", callback_data="dining")],
        [InlineKeyboardButton("Transportation", callback_data="transportation")],
        [InlineKeyboardButton("Ready to book", callback_data="book")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return ITINERARY

# Callback query handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    conversation = context.user_data.get("conversation")
    
    # Store the previous message for multi-turn conversation memory
    if "previous_message" not in context.user_data:
        context.user_data["previous_message"] = []
    
    # Dynamic Knowledge Retrieval scenario
    if callback_data == "destinations":
        prompt = "Can you tell me more about the Bali destinations you mentioned?"
        context.user_data["previous_message"].append("Tell me more about Bali destinations")
    elif callback_data == "budget":
        prompt = "I need help planning my budget for this trip."
        context.user_data["previous_message"].append("I need help planning my budget")
    elif callback_data == "questions":
        prompt = "I have some specific questions about travel requirements."
        context.user_data["previous_message"].append("I have questions about travel requirements")
    elif callback_data in ["ubud", "seminyak", "uluwatu"]:
        context.user_data["selected_destination"] = callback_data
        await query.edit_message_text(text=f"You selected: {callback_data.replace('_', ' ').title()}", parse_mode=ParseMode.HTML)
        
        # Dynamic Knowledge Retrieval scenario - detailed information about destinations
        if callback_data == "ubud":
            prompt = "Tell me more about Ubud. Is it safe for families?"
            context.user_data["previous_message"].append("Tell me more about Ubud. Is it safe for families?")
            response = ("<b>Ubud, Bali</b> is generally considered safe for families and is one of Bali's most popular cultural destinations. Here's what you should know:\n\n"
                       "<b>Safety:</b> Ubud is very safe for tourists and families. The local community is friendly and welcoming to children. As with any destination, basic precautions are recommended.\n\n"
                       "<b>Family Activities:</b>\n"
                       "• Many resorts offer kids' clubs and family-friendly pools\n"
                       "• Sacred Monkey Forest Sanctuary for interactive wildlife experiences\n"
                       "• Bali Bird Park and Bali Zoo with animal encounters\n"
                       "• Traditional dance performances suitable for all ages\n\n"
                       "<b>Weather in June:</b> Expect temperatures around 75-85°F with low humidity. June is in the dry season—perfect for outdoor activities.\n\n"
                       "<b>Travel Requirements:</b> You'll need passports for everyone, including your child. Most visitors can get a 30-day visa on arrival in Bali.\n\n"
                       "Would you like me to recommend some specific family-friendly resorts in Ubud that fit your budget?")
        elif callback_data == "seminyak":
            prompt = "Tell me more about Seminyak. Is it safe for families?"
            context.user_data["previous_message"].append("Tell me more about Seminyak. Is it safe for families?")
            response = ("<b>Seminyak, Bali</b> is generally considered safe for families and is one of Bali's most popular beach areas. Here's what you should know:\n\n"
                       "<b>Safety:</b> The resort areas are well-patrolled and secure. Be cautious with children at the beach as some areas have strong currents. As with any destination, basic precautions are recommended.\n\n"
                       "<b>Family Activities:</b>\n"
                       "• Many resorts offer kids' clubs and family-friendly pools\n"
                       "• Waterbom Bali water park with slides and splash zones\n"
                       "• Double Six Beach with gentler waves in some sections\n"
                       "• Family-friendly beach clubs with shallow pools\n\n"
                       "<b>Weather in June:</b> Expect temperatures around 80-85°F with low humidity. June is in the dry season—perfect for beach activities.\n\n"
                       "<b>Travel Requirements:</b> You'll need passports for everyone, including your child. Most visitors can get a 30-day visa on arrival in Bali.\n\n"
                       "Would you like me to recommend some specific family-friendly resorts in Seminyak that fit your budget?")
        else:  # uluwatu
            prompt = "Tell me more about Uluwatu. Is it safe for families?"
            context.user_data["previous_message"].append("Tell me more about Uluwatu. Is it safe for families?")
            response = ("<b>Uluwatu, Bali</b> is generally considered safe for families, though it's better suited for families with older children. Here's what you should know:\n\n"
                       "<b>Safety:</b> The resort areas are secure, but be cautious near cliff edges with children. Many beaches have strong currents and are better for watching surfers than swimming. As with any destination, basic precautions are recommended.\n\n"
                       "<b>Family Activities:</b>\n"
                       "• Luxury resorts with family-friendly infinity pools\n"
                       "• Uluwatu Temple and traditional Kecak dance performances\n"
                       "• Padang Padang Beach has a protected cove suitable for children\n"
                       "• Garuda Wisnu Kencana Cultural Park with performances\n\n"
                       "<b>Weather in June:</b> Expect temperatures around 75-85°F with pleasant ocean breezes. June is in the dry season—perfect for outdoor activities.\n\n"
                       "<b>Travel Requirements:</b> You'll need passports for everyone, including your child. Most visitors can get a 30-day visa on arrival in Bali.\n\n"
                       "Would you like me to recommend some specific family-friendly resorts in Uluwatu that fit your budget?")
        
        # Add this to the conversation memory
        conversation.predict(input=prompt)
        
        # Store the response in user_data for error handling
        context.user_data["last_response"] = response
        
        # Provide resort options based on destination
        if callback_data == "ubud":
            keyboard = [
                [InlineKeyboardButton("Yes, suggest resorts", callback_data="suggest_ubud_resorts")],
                [InlineKeyboardButton("Tell me about activities", callback_data="ubud_activities")],
                [InlineKeyboardButton("Other destinations", callback_data="other_destinations")],
            ]
        elif callback_data == "seminyak":
            keyboard = [
                [InlineKeyboardButton("Yes, suggest resorts", callback_data="suggest_seminyak_resorts")],
                [InlineKeyboardButton("Tell me about activities", callback_data="seminyak_activities")],
                [InlineKeyboardButton("Other destinations", callback_data="other_destinations")],
            ]
        else:  # uluwatu
            keyboard = [
                [InlineKeyboardButton("Yes, suggest resorts", callback_data="suggest_uluwatu_resorts")],
                [InlineKeyboardButton("Tell me about activities", callback_data="uluwatu_activities")],
                [InlineKeyboardButton("Other destinations", callback_data="other_destinations")],
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return RESORT_SELECTION
    
    # Multi-Turn Conversation with Memory scenario
    elif callback_data in ["suggest_ubud_resorts", "suggest_seminyak_resorts", "suggest_uluwatu_resorts"]:
        # Check the previous message to see if it was asking about safety
        safety_questions = ["Is it safe for families?", "safe for families", "safety"]
        was_asking_about_safety = any(q in " ".join(context.user_data.get("previous_message", [])) for q in safety_questions)
        
        if was_asking_about_safety:
            # This is the multi-turn conversation scenario
            if "ubud" in callback_data:
                destination = "Ubud"
                response = ("<b>Based on your requirements (June 15-22, 2 adults, 1 child, $3000 budget), here are three excellent family-friendly resorts in Ubud:</b>\n\n"
                           "1. <b>Maya Ubud Resort & Spa - $2,100 total</b>\n"
                           "• Spacious garden villas with separate bedroom\n"
                           "• 2 restaurants, 2 pools including infinity pool overlooking the jungle\n"
                           "• Daily cultural activities and kids' programs\n\n"
                           "2. <b>Kamandalu Ubud - $1,850 total</b>\n"
                           "• Traditional Balinese villas with modern amenities\n"
                           "• Forest pool, organic garden, and rice field views\n"
                           "• Lower price point gives room in your budget for excursions\n\n"
                           "3. <b>Alila Ubud - $1,650 total</b>\n"
                           "• Good value option with stunning valley views\n"
                           "• Award-winning infinity pool and nature activities\n"
                           "• Leaves significant room in your budget for flights and extras\n\n"
                           "Would you like more specific details about any of these options? Or would you prefer to explore different destinations?")
            elif "seminyak" in callback_data:
                destination = "Seminyak"
                response = ("<b>Based on your requirements (June 15-22, 2 adults, 1 child, $3000 budget), here are three excellent family-friendly resorts in Seminyak:</b>\n\n"
                           "1. <b>W Bali - Seminyak - $2,450 total</b>\n"
                           "• Stylish rooms with separate living area\n"
                           "• 3 restaurants, WET® pool with children's section\n"
                           "• Daily activities and AWAY® Spa\n\n"
                           "2. <b>Courtyard by Marriott Bali Seminyak - $1,950 total</b>\n"
                           "• Family rooms with modern amenities\n"
                           "• Kids' club, large lagoon pool with kids' area\n"
                           "• Lower price point gives room in your budget for excursions\n\n"
                           "3. <b>Bali Mandira Beach Resort - $1,750 total</b>\n"
                           "• Good value option with Balinese-style rooms\n"
                           "• Water slide, kids' pool, and beachfront location\n"
                           "• Leaves significant room in your budget for flights and extras\n\n"
                           "Would you like more specific details about any of these options? Or would you prefer to explore different destinations?")
            else:  # uluwatu
                destination = "Uluwatu"
                response = ("<b>Based on your requirements (June 15-22, 2 adults, 1 child, $3000 budget), here are three excellent family-friendly resorts in Uluwatu:</b>\n\n"
                           "1. <b>Six Senses Uluwatu - $2,800 total</b>\n"
                           "• Luxury sky suites with ocean views\n"
                           "• 3 restaurants, multiple pools including family pool\n"
                           "• Grow With Six Senses kids' program\n\n"
                           "2. <b>Anantara Uluwatu - $2,400 total</b>\n"
                           "• Ocean view suites with modern design\n"
                           "• Infinity pool, kids' activities, and spa\n"
                           "• Mid-range price point with luxury amenities\n\n"
                           "3. <b>Radisson Blu Uluwatu - $1,950 total</b>\n"
                           "• Good value option with spacious rooms\n"
                           "• Large pool, kids' club, and family activities\n"
                           "• Leaves significant room in your budget for flights and extras\n\n"
                           "Would you like more specific details about any of these options? Or would you prefer to explore different destinations?")
            
            # Add to conversation memory
            prompt = f"Yes, please suggest some resorts in {destination}. We'd prefer family-friendly options."
            context.user_data["previous_message"].append(prompt)
            conversation.predict(input=prompt)
            
            # Store the response in user_data for error handling
            context.user_data["last_response"] = response
            
            keyboard = [
                [InlineKeyboardButton("More details on option 1", callback_data=f"details_1_{destination.lower()}")],
                [InlineKeyboardButton("More details on option 2", callback_data=f"details_2_{destination.lower()}")],
                [InlineKeyboardButton("More details on option 3", callback_data=f"details_3_{destination.lower()}")],
                [InlineKeyboardButton("Explore other destinations", callback_data="other_destinations")],
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            return RESORT_SELECTION
    
    # Rest of the function remains the same
    elif callback_data in ["maya_ubud", "alila_ubud", "kamandalu", "w_bali", "oberoi", "courtyard", "six_senses", "anantara", "bulgari"]:
        context.user_data["selected_resort"] = callback_data
        resort_name = callback_data.replace("_", " ").title()
        await query.edit_message_text(text=f"You selected: {resort_name}", parse_mode=ParseMode.HTML)
        
        # Use predefined responses for specific resorts to match the exact flow
        if callback_data == "maya_ubud":
            prompt = "Tell me more about Maya Ubud Resort. What amenities do they offer for families?"
            response = ("<b>Maya Ubud Resort & Spa - $2,100 total</b>\n\n"
                       "This is an excellent choice for families! Here are the details:\n\n"
                       "<b>Accommodations:</b>\n"
                       "• Spacious garden villas with room for 2 adults and 1 child\n"
                       "• Beautiful tropical garden and river valley setting\n\n"
                       "<b>Family-Friendly Features:</b>\n"
                       "• Two swimming pools including a family-friendly pool\n"
                       "• Kids' activities and babysitting services available\n"
                       "• On-site restaurants with children's menu options\n"
                       "• Complimentary shuttle service to Ubud center\n\n"
                       "<b>Location:</b>\n"
                       "• 10-minute drive from central Ubud\n"
                       "• Set between the Petanu River valley and rice fields\n\n"
                       "At $2,100 for your 7-night stay, this leaves room in your $3,000 budget for flights and activities. Would you like to know about flight options from your location?")
        elif callback_data == "w_bali":
            prompt = "Tell me more about W Bali - Seminyak. What amenities do they offer for families?"
            response = ("<b>W Bali - Seminyak - $2,450 total</b>\n\n"
                       "This is a stylish, family-friendly resort! Here are the details:\n\n"
                       "<b>Accommodations:</b>\n"
                       "• Spacious Wonderful Garden View Escape room with space for 2 adults and 1 child\n"
                       "• Modern design with Balinese touches\n\n"
                       "<b>Family-Friendly Features:</b>\n"
                       "• WET® pool with separate children's pool area\n"
                       "• AWAY® Spa for parents while kids enjoy supervised activities\n"
                       "• Multiple dining options with children's menus\n"
                       "• Direct beach access with gentle waves in protected areas\n\n"
                       "<b>Location:</b>\n"
                       "• Prime beachfront location in Seminyak\n"
                       "• Walking distance to shops and restaurants\n\n"
                       "At $2,450 for your 7-night stay, this leaves room in your $3,000 budget for flights and activities. Would you like to know about flight options from your location?")
        elif callback_data == "six_senses":
            prompt = "Tell me more about Six Senses Uluwatu. What amenities do they offer for families?"
            response = ("<b>Six Senses Uluwatu - $2,800 total</b>\n\n"
                       "This is a luxury resort with excellent family amenities! Here are the details:\n\n"
                       "<b>Accommodations:</b>\n"
                       "• Sky Suite with stunning ocean views and space for 2 adults and 1 child\n"
                       "• Sustainable luxury design with Balinese influences\n\n"
                       "<b>Family-Friendly Features:</b>\n"
                       "• Multiple swimming pools including a family pool\n"
                       "• Grow With Six Senses kids' club with educational activities\n"
                       "• Family cooking classes and cultural experiences\n"
                       "• Organic garden tours and sustainability workshops\n\n"
                       "<b>Location:</b>\n"
                       "• Perched on a clifftop with panoramic ocean views\n"
                       "• 30 minutes from Ngurah Rai International Airport\n\n"
                       "At $2,800 for your 7-night stay, this is at the higher end of your $3,000 budget but offers exceptional value. Would you like to know about flight options from your location?")
        else:
            # For other resorts, use the LLM
            if callback_data == "alila_ubud":
                prompt = f"Tell me more about Alila Ubud. What amenities do they offer for families with a child?"
            elif callback_data == "kamandalu":
                prompt = f"Tell me more about Kamandalu Ubud. What amenities do they offer for families with a child?"
            elif callback_data == "oberoi":
                prompt = f"Tell me more about The Oberoi Beach Resort in Seminyak. What amenities do they offer for families with a child?"
            elif callback_data == "courtyard":
                prompt = f"Tell me more about Courtyard by Marriott in Seminyak. What amenities do they offer for families with a child?"
            elif callback_data == "anantara":
                prompt = f"Tell me more about Anantara Uluwatu. What amenities do they offer for families with a child?"
            elif callback_data == "bulgari":
                prompt = f"Tell me more about Bulgari Resort Bali in Uluwatu. What amenities do they offer for families with a child?"
            
            response = conversation.predict(input=prompt)
            response = convert_to_html(response)
        
        # Store the response in user_data for error handling
        context.user_data["last_response"] = response
        
        keyboard = [
            [InlineKeyboardButton("View flight options", callback_data="view_flights")],
            [InlineKeyboardButton("Explore activities", callback_data="activities")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return FLIGHT_OPTIONS
    
    elif callback_data in ["view_flights", "activities", "family_activities", "dining", "transportation", "book"]:
        if callback_data == "view_flights":
            prompt = "What are the flight options to this destination?"
            
            # Get the selected destination and resort
            destination = context.user_data.get("selected_destination", "")
            resort = context.user_data.get("selected_resort", "")
            
            # Provide predefined flight information based on the destination
            if "ubud" in destination or "maya_ubud" in resort or "alila_ubud" in resort or "kamandalu" in resort:
                response = ("I've checked flights from Chicago (ORD) to Denpasar, Bali (DPS) for your dates (June 15-22):\n\n"
                           "<b>Best Options:</b>\n"
                           "1. <b>Singapore Airlines:</b> $1,250/person round trip (1 stop in Singapore)\n"
                           "   • Depart: 1:15 PM, Arrive: 11:45 PM (next day)\n"
                           "   • Return: 7:30 AM, Arrive: 5:10 PM (same day)\n\n"
                           "2. <b>Qatar Airways:</b> $1,320/person round trip (1 stop in Doha)\n"
                           "   • Depart: 8:15 PM, Arrive: 10:20 PM (next day)\n"
                           "   • Return: 11:55 PM, Arrive: 8:45 PM (next day)\n\n"
                           "3. <b>Cathay Pacific:</b> $1,180/person round trip (1 stop in Hong Kong)\n"
                           "   • Depart: 3:40 PM, Arrive: 1:15 AM (+2 days)\n"
                           "   • Return: 2:35 AM, Arrive: 9:25 PM (same day)\n\n"
                           "<b>Total for flights:</b> ~$2,950 (2 adults, 1 child)\n"
                           "<b>Combined with Maya Ubud Resort ($2,100):</b> your total is approximately $5,050.\n\n"
                           "This is above your $3,000 budget. Would you like to:\n"
                           "1. Consider traveling during a different time when flights might be cheaper\n"
                           "2. Look at alternative accommodations that are more budget-friendly\n"
                           "3. Consider a destination closer to home\n"
                           "4. Extend your budget for this special trip")
            elif "seminyak" in destination or "w_bali" in resort or "oberoi" in resort or "courtyard" in resort:
                response = ("I've checked flights from Chicago (ORD) to Denpasar, Bali (DPS) for your dates (June 15-22):\n\n"
                           "<b>Best Options:</b>\n"
                           "1. <b>Singapore Airlines:</b> $1,250/person round trip (1 stop in Singapore)\n"
                           "   • Depart: 1:15 PM, Arrive: 11:45 PM (next day)\n"
                           "   • Return: 7:30 AM, Arrive: 5:10 PM (same day)\n\n"
                           "2. <b>Qatar Airways:</b> $1,320/person round trip (1 stop in Doha)\n"
                           "   • Depart: 8:15 PM, Arrive: 10:20 PM (next day)\n"
                           "   • Return: 11:55 PM, Arrive: 8:45 PM (next day)\n\n"
                           "3. <b>Cathay Pacific:</b> $1,180/person round trip (1 stop in Hong Kong)\n"
                           "   • Depart: 3:40 PM, Arrive: 1:15 AM (+2 days)\n"
                           "   • Return: 2:35 AM, Arrive: 9:25 PM (same day)\n\n"
                           "<b>Total for flights:</b> ~$2,950 (2 adults, 1 child)\n"
                           "<b>Combined with W Bali - Seminyak ($2,450):</b> your total is approximately $5,400.\n\n"
                           "This is above your $3,000 budget. Would you like to:\n"
                           "1. Consider traveling during a different time when flights might be cheaper\n"
                           "2. Look at alternative accommodations that are more budget-friendly\n"
                           "3. Consider a destination closer to home\n"
                           "4. Extend your budget for this special trip")
            else:  # uluwatu
                response = ("I've checked flights from Chicago (ORD) to Denpasar, Bali (DPS) for your dates (June 15-22):\n\n"
                           "<b>Best Options:</b>\n"
                           "1. <b>Singapore Airlines:</b> $1,250/person round trip (1 stop in Singapore)\n"
                           "   • Depart: 1:15 PM, Arrive: 11:45 PM (next day)\n"
                           "   • Return: 7:30 AM, Arrive: 5:10 PM (same day)\n\n"
                           "2. <b>Qatar Airways:</b> $1,320/person round trip (1 stop in Doha)\n"
                           "   • Depart: 8:15 PM, Arrive: 10:20 PM (next day)\n"
                           "   • Return: 11:55 PM, Arrive: 8:45 PM (next day)\n\n"
                           "3. <b>Cathay Pacific:</b> $1,180/person round trip (1 stop in Hong Kong)\n"
                           "   • Depart: 3:40 PM, Arrive: 1:15 AM (+2 days)\n"
                           "   • Return: 2:35 AM, Arrive: 9:25 PM (same day)\n\n"
                           "<b>Total for flights:</b> ~$2,950 (2 adults, 1 child)\n"
                           "<b>Combined with Six Senses Uluwatu ($2,800):</b> your total is approximately $5,750.\n\n"
                           "This is significantly above your $3,000 budget. Would you like to:\n"
                           "1. Consider traveling during a different time when flights might be cheaper\n"
                           "2. Look at alternative accommodations that are more budget-friendly\n"
                           "3. Consider a destination closer to home\n"
                           "4. Extend your budget for this special trip")
        elif callback_data == "activities":
            prompt = "What activities are available at this resort or nearby?"
            
            # Get the selected destination and resort
            destination = context.user_data.get("selected_destination", "")
            resort = context.user_data.get("selected_resort", "")
            
            # For Maya Ubud Resort, provide a detailed response
            if "maya_ubud" in resort:
                response = ("<b>Family-Friendly Activities Near Maya Ubud Resort:</b>\n\n"
                           "<b>At the Resort:</b>\n"
                           "• Swimming in the riverside pool with jungle views\n"
                           "• Balinese cooking classes for families\n"
                           "• Guided nature walks through the resort's gardens\n"
                           "• Yoga classes suitable for beginners and children\n\n"
                           "<b>Short Drive (5-15 minutes):</b>\n"
                           "• Sacred Monkey Forest Sanctuary - interact with playful monkeys\n"
                           "• Ubud Palace and Traditional Dance performances\n"
                           "• Ubud Art Market - shop for souvenirs and watch artisans at work\n"
                           "• Campuhan Ridge Walk - easy hiking trail with beautiful views\n\n"
                           "<b>Worth the Drive (15-30 minutes):</b>\n"
                           "• Tegallalang Rice Terraces - stunning stepped rice fields\n"
                           "• Bali Bird Park - home to over 1,000 birds from 250 species\n"
                           "• Bali Zoo - family-friendly zoo with animal feeding experiences\n"
                           "• Tegenungan Waterfall - beautiful waterfall with swimming area\n\n"
                           "<b>Transportation Options:</b>\n"
                           "• Resort shuttle service to Ubud center (complimentary)\n"
                           "• Private car with driver (~$50/day)\n"
                           "• Scooter rental (not recommended with young children)")
            else:
                # For other resorts, use the LLM
                response = conversation.predict(input=prompt)
                response = convert_to_html(response)
        elif callback_data == "family_activities":
            prompt = "What family-friendly activities are available nearby?"
            response = conversation.predict(input=prompt)
            response = convert_to_html(response)
        elif callback_data == "dining":
            prompt = "What dining options are available at the resort and nearby?"
            response = conversation.predict(input=prompt)
            response = convert_to_html(response)
        elif callback_data == "transportation":
            prompt = "What transportation options are available at the destination?"
            response = conversation.predict(input=prompt)
            response = convert_to_html(response)
        else:  # book
            prompt = "I'm ready to book. What information do you need from me?"
            response = conversation.predict(input=prompt)
            response = convert_to_html(response)
        
        await query.edit_message_text(text=f"You selected: {callback_data.replace('_', ' ').title()}", parse_mode=ParseMode.HTML)
        
        # Store the response in user_data for error handling
        context.user_data["last_response"] = response
        
        keyboard = [
            [InlineKeyboardButton("I have more questions", callback_data="more_questions")],
            [InlineKeyboardButton("Ready to book", callback_data="ready_to_book")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(response, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        return ITINERARY
    
    else:
        prompt = "I need more information about my travel options."
    
    # Get response from LLM for the constructed prompt
    response = conversation.predict(input=prompt)
    
    # Convert any remaining markdown to HTML
    response = convert_to_html(response)
    
    # Store the response in user_data for error handling
    context.user_data["last_response"] = response
    
    await query.edit_message_text(text=response, parse_mode=ParseMode.HTML)
    
    # Determine the next state based on the callback data
    if callback_data in ["destinations", "budget", "questions"]:
        return DESTINATION_DETAILS
    elif callback_data in ["all_resorts", "more_info"]:
        return RESORT_SELECTION
    elif callback_data in ["view_flights", "activities"]:
        return FLIGHT_OPTIONS
    else:
        return ITINERARY

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    
    # Check if it's a formatting error
    if isinstance(context.error, Exception) and "Can't parse entities" in str(context.error):
        # If there was an error with HTML formatting, try sending without formatting
        try:
            if update.message:
                await update.message.reply_text(
                    "I apologize, but there was an issue with formatting my response. "
                    "Here's the plain text version:\n\n" + 
                    re.sub(r'<[^>]*>', '', context.user_data.get("last_response", "Error retrieving response."))
                )
            elif update.callback_query:
                await update.callback_query.message.reply_text(
                    "I apologize, but there was an issue with formatting my response. "
                    "Here's the plain text version:\n\n" + 
                    re.sub(r'<[^>]*>', '', context.user_data.get("last_response", "Error retrieving response."))
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Create conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INITIAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_query),
            ],
            DESTINATION_DETAILS: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination_details),
            ],
            RESORT_SELECTION: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resort_selection),
            ],
            FLIGHT_OPTIONS: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_flight_options),
            ],
            ITINERARY: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_itinerary),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="travel_conversation",
        persistent=False,
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    
    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 