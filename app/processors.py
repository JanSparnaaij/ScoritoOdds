def process_football_matches(matches):
    """
    Process the fetched football match data.

    Args:
        matches (list): List of dictionaries containing raw match data.

    Returns:
        list: Processed match data.
    """
    processed_matches = []
    for match in matches:
        try:
            # Add a timestamp to each match
            # ch["processed_at"] = "2025-01-16"  # Example, use dynamic timestamps in production

            # Example: Filter out matches with invalid odds
            if any(float(odd) <= 1.0 for odd in match["odds"].values()):
                continue

            # Standardize odds to floats
            match["odds"] = {key: float(value) for key, value in match["odds"].items()}

            processed_matches.append(match)
        except Exception as e:
            print(f"Error processing match: {e}")
            continue

    return processed_matches


def process_tennis_matches(matches):
    """
    Process the fetched tennis match data.

    Args:
        matches (list): List of dictionaries containing raw tennis match data.

    Returns:
        list: Processed match data.
    """
    processed_matches = []
    for match in matches:
        try:
            # Validate player names
            match["home_category"] = match.get("home_category", "Unknown")
            match["away_category"] = match.get("away_category", "Unknown")

            # Fill in placeholder fields if needed
            if match["date"] == "Unknown":
                match["date"] = "Unknown"  # Replace with dynamic date logic

            if match["round"] == "R?":
                match["round"] = "Unknown"  # Replace with actual round data if available

            # Enrich the data with additional info (e.g., win probabilities)
            total_expected_points = (
                match["expected_points"]["home"] + match["expected_points"]["away"]
            )
            match["win_probability"] = {
                "home": round(match["expected_points"]["home"] / total_expected_points, 2),
                "away": round(match["expected_points"]["away"] / total_expected_points, 2),
            }

            processed_matches.append(match)
        except Exception as e:
            print(f"Error processing match: {e}")
            continue

    return processed_matches
