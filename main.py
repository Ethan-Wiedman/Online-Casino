
from drafter import *
from random import randint


# -----------------------------------------
# DATA CLASS AND WEBSITE STATE
# -----------------------------------------

@dataclass
class CasinoState:
    balance: int = 5000

    # Blackjack information
    blackjack_hands: list = None
    blackjack_bets: list = None
    dealer_hand: list = None
    active_hand: int = 0
    blackjack_phase: str = "waiting"
    blackjack_message: str = ""
    blackjack_natural: bool = False
    blackjack_split_aces: bool = False
    
    #Highlow information
    highlow_first_card: int = 0
    highlow_phase: str = "waiting"


    # Other game messages
    roulette_message: str = ""
    highlow_message: str = ""
    slots_message: str = ""


# -----------------------------------------
# GENERAL HELPER FUNCTIONS
# -----------------------------------------

def get_bet(bet: str, balance: int) -> int:
    """
    Check whether a bet is valid.
    Return the bet if valid, otherwise return 0.
    """
    try:
        amount = int(bet)
    except:
        return 0

    if amount <= 0:
        return 0
    elif amount > balance:
        return 0
    else:
        return amount


def card_value(card: int) -> int:
    """
    Return the Blackjack value of a card.
    """
    if card == 1:
        return 11
    elif card >= 11:
        return 10
    else:
        return card


def hand_value(hand: list) -> int:
    """
    Calculate the value of a Blackjack hand.
    Aces can count as either 1 or 11.
    """
    total = 0
    aces = 0

    for card in hand:
        total += card_value(card)

        if card == 1:
            aces += 1

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


def card_name(card: int) -> str:
    """
    Convert a card number into a readable card name.
    """
    if card == 1:
        return "Ace"
    elif card == 11:
        return "Jack"
    elif card == 12:
        return "Queen"
    elif card == 13:
        return "King"
    else:
        return str(card)



def hand_to_string(hand: list) -> str:
    """
    Convert a list of cards into a readable string.
    Each card appears on its own line.
    """
    result = ""

    for card in hand:
        result += card_name(card) + "\n"

    return result



def draw_card() -> int:
    """
    Draw a random card from 1 through 13.
    """
    return randint(1, 13)


# -----------------------------------------
# HOME PAGE
# -----------------------------------------

@route
def index(state: CasinoState) -> Page:
    return Page(state, [
        "WELCOME TO THE ONLINE CASINO!",
        "",
        "Your current balance: $" + str(state.balance),
        "",
        "Choose a game:",
        Button("Blackjack", "/blackjack_page"),
        Button("Roulette", "/roulette_page"),
        Button("High-Low", "/highlow_page"),
        Button("Slot Machine", "/slots_page"),
        Button("Game Rules", "/rules_page")
    ])


# -----------------------------------------
# BLACKJACK
# -----------------------------------------


def blackjack_screen(state: CasinoState) -> Page:
    """
    Display the Blackjack game.
    """

    content = [
        "BLACKJACK",
        "",
        "Your balance: $" + str(state.balance),
        ""
    ]

    if state.blackjack_phase == "waiting":
        content.append("Enter your bet to start playing.")
        content.append(TextBox("bet", default_value="100"))
        content.append(Button("Deal Cards", "/blackjack_deal"))

    elif state.blackjack_phase == "playing":

        content.append("DEALER'S HAND:")
        content.append(card_name(state.dealer_hand[0]))
        content.append("")

        content.append("YOUR HAND:")

        for card in state.blackjack_hands[state.active_hand]:
            content.append(card_name(card))

        content.append("")
        content.append(
            "Hand value: " +
            str(hand_value(state.blackjack_hands[state.active_hand]))
        )

        content.append(
            "Current bet: $" +
            str(state.blackjack_bets[state.active_hand])
        )

        content.append(
            "Playing hand " +
            str(state.active_hand + 1) +
            " of " +
            str(len(state.blackjack_hands))
        )

        content.append("")

        content.append(Button("Hit", "/blackjack_hit"))
        content.append(Button("Stand", "/blackjack_stand"))
        content.append(Button("Double Down", "/blackjack_double"))

        if (len(state.blackjack_hands) == 1
                and len(state.blackjack_hands[0]) == 2
                and state.blackjack_hands[0][0] ==
                state.blackjack_hands[0][1]
                and state.balance >= state.blackjack_bets[0]):

            content.append(Button("Split", "/blackjack_split"))

    else:
        content.append("DEALER'S HAND:")

        for card in state.dealer_hand:
            content.append(card_name(card))

        content.append(
            "Dealer value: " + str(hand_value(state.dealer_hand))
        )

        content.append("")

        for i in range(len(state.blackjack_hands)):
            content.append("YOUR HAND " + str(i + 1) + ":")

            for card in state.blackjack_hands[i]:
                content.append(card_name(card))

            content.append(
                "Value: " + str(hand_value(state.blackjack_hands[i]))
            )

            content.append("")

        content.append(state.blackjack_message)
        content.append(Button("Play Again", "/blackjack_page"))

    content.append("")
    content.append(Button("Return Home", "/"))

    return Page(state, content)



@route
def blackjack_page(state: CasinoState) -> Page:
    state.blackjack_phase = "waiting"
    state.blackjack_message = ""
    return blackjack_screen(state)


@route
def blackjack_deal(state: CasinoState, bet: str) -> Page:
    amount = get_bet(bet, state.balance)

    if amount == 0:
        state.blackjack_message = "Invalid bet. Please try again."
        state.blackjack_phase = "waiting"
        return blackjack_screen(state)

    state.balance -= amount

    state.blackjack_hands = [
        [draw_card(), draw_card()]
    ]

    state.blackjack_bets = [amount]

    state.dealer_hand = [
        draw_card(), draw_card()
    ]

    state.active_hand = 0
    state.blackjack_phase = "playing"
    state.blackjack_split_aces = False

    state.blackjack_natural = (
        hand_value(state.blackjack_hands[0]) == 21
    )

    # Check for an immediate Blackjack.
    if state.blackjack_natural:
        finish_blackjack(state)

    return blackjack_screen(state)


def finish_blackjack(state: CasinoState):
    """
    Play the dealer's hand and calculate the results.
    """

    # Dealer draws until reaching 17 or higher.
    while hand_value(state.dealer_hand) < 17:
        state.dealer_hand.append(draw_card())

    dealer_total = hand_value(state.dealer_hand)
    dealer_natural = (
        len(state.dealer_hand) == 2 and dealer_total == 21
    )

    message = ""

    for i in range(len(state.blackjack_hands)):

        player_total = hand_value(state.blackjack_hands[i])
        bet = state.blackjack_bets[i]

        message += "Hand " + str(i + 1) + ": "

        if player_total > 21:
            message += "You busted and lost $" + str(bet) + ". "

        elif (state.blackjack_natural
              and len(state.blackjack_hands) == 1
              and not dealer_natural):

            winnings = bet * 5 // 2
            state.balance += winnings
            message += "Natural Blackjack! You won $" + str(winnings - bet) + ". "

        elif dealer_natural and player_total == 21:
            state.balance += bet
            message += "Push! Your bet was returned. "

        elif dealer_total > 21:
            state.balance += bet * 2
            message += "Dealer busted! You won $" + str(bet) + ". "

        elif player_total > dealer_total:
            state.balance += bet * 2
            message += "You won $" + str(bet) + ". "

        elif player_total == dealer_total:
            state.balance += bet
            message += "Push! Your bet was returned. "

        else:
            message += "Dealer wins. You lost $" + str(bet) + ". "

    state.blackjack_message = message
    state.blackjack_phase = "finished"


def advance_blackjack(state: CasinoState):
    """
    Move to the next hand or finish the game.
    """

    if state.active_hand + 1 < len(state.blackjack_hands):
        state.active_hand += 1
    else:
        finish_blackjack(state)


@route
def blackjack_hit(state: CasinoState) -> Page:

    if state.blackjack_phase == "playing":

        if state.blackjack_split_aces:
            state.blackjack_message = "Split Aces can only receive one additional card."
            return blackjack_screen(state)

        state.blackjack_hands[state.active_hand].append(draw_card())

        total = hand_value(state.blackjack_hands[state.active_hand])

        if total >= 21:
            advance_blackjack(state)

    return blackjack_screen(state)


@route
def blackjack_stand(state: CasinoState) -> Page:

    if state.blackjack_phase == "playing":
        advance_blackjack(state)

    return blackjack_screen(state)


@route
def blackjack_double(state: CasinoState) -> Page:

    if state.blackjack_phase == "playing":

        hand = state.blackjack_hands[state.active_hand]
        bet = state.blackjack_bets[state.active_hand]

        if len(hand) != 2:
            state.blackjack_message = "You can only double down on your first two cards."

        elif state.balance < bet:
            state.blackjack_message = "You don't have enough money to double down."

        else:
            state.balance -= bet
            state.blackjack_bets[state.active_hand] *= 2

            hand.append(draw_card())

            advance_blackjack(state)

    return blackjack_screen(state)


@route
def blackjack_split(state: CasinoState) -> Page:

    if state.blackjack_phase == "playing":

        hand = state.blackjack_hands[0]
        bet = state.blackjack_bets[0]

        if len(hand) == 2 and hand[0] == hand[1]:

            if state.balance >= bet:

                state.balance -= bet

                first_card = hand[0]
                second_card = hand[1]

                state.blackjack_hands = [
                    [first_card, draw_card()],
                    [second_card, draw_card()]
                ]

                state.blackjack_bets = [bet, bet]
                state.active_hand = 0

                # Split Aces receive one card each and automatically stand.
                if first_card == 1:
                    state.blackjack_split_aces = True
                    finish_blackjack(state)

            else:
                state.blackjack_message = "Not enough money to split."

    return blackjack_screen(state)


# -----------------------------------------
# ROULETTE
# -----------------------------------------

@route
def roulette_page(state: CasinoState) -> Page:

    return Page(state, [
        "ROULETTE",
        "",
        "Your balance: $" + str(state.balance),
        "",
        "Choose a number between 0 and 36.",
        "If the roulette wheel lands on your number, you win!",
        "",
        "Enter your bet:",
        TextBox("bet", default_value="100"),
        "",
        "Enter your number:",
        TextBox("number", default_value="7"),
        "",
        Button("Spin Wheel", "/roulette_play"),
        "",
        state.roulette_message,
        "",
        Button("Return Home", "/")
    ])


@route
def roulette_play(state: CasinoState, bet: str, number: str) -> Page:

    amount = get_bet(bet, state.balance)

    try:
        guess = int(number)
    except:
        guess = -1

    if amount == 0:
        state.roulette_message = "Invalid bet."

    elif guess < 0 or guess > 36:
        state.roulette_message = "Choose a number between 0 and 36."

    else:
        state.balance -= amount

        result = randint(0, 36)

        if result == guess:
            winnings = amount * 36
            state.balance += winnings

            state.roulette_message = (
                "The wheel landed on " + str(result) +
                "! You won $" + str(winnings - amount) + "!"
            )

        else:
            state.roulette_message = (
                "The wheel landed on " + str(result) +
                ". You lost $" + str(amount) + "."
            )

    return roulette_page(state)


# -----------------------------------------
# HIGH-LOW
# -----------------------------------------


# -----------------------------------------
# HIGH-LOW
# -----------------------------------------



@route
def highlow_page(state: CasinoState) -> Page:

    content = [
        "HIGH-LOW",
        "",
        "Your balance: $" + str(state.balance),
        ""
    ]

    if state.highlow_phase == "waiting":

        content.append("Enter your bet:")
        content.append(TextBox("bet", default_value="100"))
        content.append(Button("Start Game", "/highlow_start"))

    elif state.highlow_phase == "guessing":

        content.append("YOUR FIRST CARD:")
        content.append(card_name(state.highlow_first_card))
        content.append("")

        content.append("Will the next card be higher or lower?")
        content.append(Button("Higher", "/highlow_higher"))
        content.append(Button("Lower", "/highlow_lower"))

    else:

        content.append(state.highlow_message)
        content.append(Button("Play Again", "/highlow_reset"))

    content.append("")
    content.append(Button("Return Home", "/"))

    return Page(state, content)



@route
def highlow_start(state: CasinoState, bet: str) -> Page:

    amount = get_bet(bet, state.balance)

    if amount == 0:

        state.highlow_message = "Invalid bet."
        state.highlow_phase = "finished"

    else:

        state.balance -= amount

        state.highlow_first_card = randint(2, 14)
        state.highlow_phase = "guessing"

        # Store the bet for the next step.
        state.highlow_message = str(amount)

    return highlow_page(state)


@route
def highlow_higher(state: CasinoState) -> Page:

    return highlow_result(state, "higher")


@route
def highlow_lower(state: CasinoState) -> Page:

    return highlow_result(state, "lower")


def highlow_result(state: CasinoState, guess: str) -> Page:

    if state.highlow_phase == "guessing":

        amount = int(state.highlow_message)

        first_card = state.highlow_first_card
        second_card = randint(2, 14)

        first_name = card_name(first_card)
        second_name = card_name(second_card)

        if second_card == first_card:

            state.balance += amount

            state.highlow_message = (
                "First card: " + first_name +
                "\nSecond card: " + second_name +
                "\nIt's a tie! Your bet was returned."
            )

        elif ((guess == "higher" and second_card > first_card)
              or (guess == "lower" and second_card < first_card)):

            state.balance += amount * 2

            state.highlow_message = (
                "First card: " + first_name +
                "\nSecond card: " + second_name +
                "\nCorrect! You won $" + str(amount) + "!"
            )

        else:

            state.highlow_message = (
                "First card: " + first_name +
                "\nSecond card: " + second_name +
                "\nIncorrect! You lost $" + str(amount) + "."
            )

        state.highlow_phase = "finished"

    return highlow_page(state)


@route
def highlow_reset(state: CasinoState) -> Page:

    state.highlow_phase = "waiting"
    state.highlow_message = ""

    return highlow_page(state)


# -----------------------------------------
# SLOT MACHINE
# -----------------------------------------

@route
def slots_page(state: CasinoState) -> Page:

    return Page(state, [
        "SLOT MACHINE",
        "",
        "Your balance: $" + str(state.balance),
        "",
        "Three matching symbols pay 10 times your bet.",
        "Two matching symbols pay 2 times your bet.",
        "",
        "Enter your bet:",
        TextBox("bet", default_value="100"),
        "",
        Button("Spin!", "/slots_play"),
        "",
        state.slots_message,
        "",
        Button("Return Home", "/")
    ])


@route
def slots_play(state: CasinoState, bet: str) -> Page:

    amount = get_bet(bet, state.balance)

    if amount == 0:
        state.slots_message = "Invalid bet."

    else:
        state.balance -= amount

        symbols = [
            "Cherry",
            "Lemon",
            "Bell",
            "Star",
            "Seven"
        ]

        first = randint(0, 4)
        second = randint(0, 4)
        third = randint(0, 4)

        result = (
            symbols[first] + " | " +
            symbols[second] + " | " +
            symbols[third]
        )

        if first == second and second == third:
            winnings = amount * 10
            state.balance += winnings

            state.slots_message = (
                result + " - JACKPOT! You won $" +
                str(winnings - amount) + "!"
            )

        elif first == second or first == third or second == third:
            winnings = amount * 2
            state.balance += winnings

            state.slots_message = (
                result + " - Two matching symbols! You won $" +
                str(winnings - amount) + "!"
            )

        else:
            state.slots_message = (
                result + " - No match! You lost $" +
                str(amount) + "."
            )

    return slots_page(state)


# -----------------------------------------
# GAME RULES PAGE
# -----------------------------------------

@route
def rules_page(state: CasinoState) -> Page:

    return Page(state, [
        "GAME RULES" ,
        "\n",
        "BLACKJACK",
        "The goal is to get a hand value as close to 21 as possible "
        "without going over.",
        "Number cards are worth their face value. Face cards are worth 10. "
        "Aces are worth 1 or 11.",
        "You can hit, stand, double down, or split matching cards.",
        "The dealer must draw until reaching 17.",
        "A natural Blackjack pays 3:2.\n",
        "\n",
        "ROULETTE",
        "Choose a number between 0 and 36.",
        "The wheel randomly selects a number.",
        "If your number matches the result, you receive 35:1 odds "
        "in addition to your returned bet.",
        "\n",
        "HIGH-LOW",
        "Two cards are drawn.",
        "Guess whether the second card will be higher or lower "
        "than the first.",
        "A correct guess doubles your bet.",
        "A tie returns your bet.",
        "\n",
        "SLOT MACHINE",
        "Three random symbols are generated.",
        "Three matching symbols pay 10 times your bet.",
        "Two matching symbols pay 2 times your bet.",
        "No matching symbols means you lose your bet.",
        "",
        Button("Return Home", "/")
    ])


# -----------------------------------------
# START THE WEBSITE
# -----------------------------------------

start_server(CasinoState())

