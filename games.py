import random


def spin_roulette(amount: int, choice: str):
    spin = random.randint(0, 36)
    if spin == 0:
        color = "green"
    elif spin % 2 == 0:
        color = "black"
    else:
        color = "red"

    win = False
    payout = 0
    if choice == "green" and color == "green":
        win = True
        payout = amount * 14
    elif choice in {"red", "black"} and color == choice:
        win = True
        payout = amount * 2

    result_name = "Ganaste" if win else "Perdiste"
    return win, payout, result_name, f"{spin} {color.title()}"


def _card_value(card: str):
    if card in {"J", "Q", "K"}:
        return 10
    if card == "A":
        return 11
    return int(card)


def _hand_score(cards):
    total = sum(_card_value(card) for card in cards)
    aces = cards.count("A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def _draw_card():
    deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    return random.choice(deck)


def _format_hand(cards):
    return " ".join(cards)


def play_blackjack(bet: int):
    player = [_draw_card(), _draw_card()]
    dealer = [_draw_card(), _draw_card()]

    player_score = _hand_score(player)
    dealer_score = _hand_score(dealer)

    while dealer_score < 17:
        dealer.append(_draw_card())
        dealer_score = _hand_score(dealer)

    result = ""
    net_change = 0

    if player_score > 21:
        result = "Te pasaste. Perdías la apuesta."
        net_change = -bet
    elif dealer_score > 21:
        result = "El dealer se pasó. Ganaste!"
        net_change = bet
    elif player_score == dealer_score:
        result = "Empate. Recuperas tu apuesta."
        net_change = 0
    elif player_score == 21 and len(player) == 2:
        result = "Blackjack! Ganaste 1.5x tu apuesta."
        net_change = int(bet * 1.5)
    elif player_score > dealer_score:
        result = "Ganaste al dealer."
        net_change = bet
    else:
        result = "Perdiste contra el dealer."
        net_change = -bet

    description = (
        f"Tu puntaje: {player_score}\n"
        f"Dealer puntaje: {dealer_score}\n"
        f"Apuesta: {bet} PieraCoin"
    )

    return {
        "player_hand": _format_hand(player),
        "dealer_hand": _format_hand(dealer),
        "result": result,
        "description": description,
        "net_change": net_change,
    }
