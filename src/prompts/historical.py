HISTORICAL_PROMPT = """You are an expert in archaeogenetics, anthropology, and ancient history. Your task is to reconstruct the world of a hypothetical individual from the past based on the provided data.

**Input:**
1.  **[GEOGRAPHICAL_DESCRIPTION]:** {geographical_description}
2.  **[TIME_PERIOD]:** {time_period}
3.  **[SEX]:** {sex} (F - female, M - male).

**Task:**
Analyze the inputs to generate a detailed profile of this individual's world. 
The output MUST be a single, valid JSON object. 
The keys in the JSON object MUST be in English, as specified in the structure below.
The contexts and occupations keys must be strictly separate; do not mix their content.

**Instructions for contexts:**
Fill in each context section with broad background information about the individual's world. 
This section should describe the environment, population, and historical situation, NOT specific jobs.

**Instructions for occupations:**
Generate a list of 7-10 plausible occupations for an individual of the specified [SEX].
For each occupation, provide a single-sentence description explaining the role.
Ensure the list represents different social strata. Include roles for: a) nobility/elites, b) artisans/merchants/specialists, and c) commoners/farmers. Explicitly EXCLUDE roles related to slavery.

**JSON Structure:**
{{
  "contexts": {{
    "genetic": {{
      "description": "A narrative description of the individual's genetic background and lineage within the region.",
      "facts": [
        "Fact 1 about genetic continuity.",
        "Fact 2 about specific haplogroups or ancestral components.",
        "Fact 3...",
        "Fact 4...",
        "Fact 5..."
      ]
    }},
    "population": {{
      "description": "A description of the broader population group, its connections, and migrations.",
      "facts": [
        "Fact 1 about population clusters and neighbors.",
        "Fact 2 about migration waves that shaped the population.",
        "Fact 3...",
        "Fact 4...",
        "Fact 5..."
      ]
    }},
    "historical_cultural": {{
      "description": "A description of the major cultural shifts occurring during the individual's lifetime.",
      "facts": [
        "Fact 1 about the transition between major eras (e.g., Bronze to Iron Age).",
        "Fact 2 about changes in technology or social structure.",
        "Fact 3...",
        "Fact 4...",
        "Fact 5..."
      ]
    }},
    "archaeological": {{
      "description": "A detailed description of the typical burial practices for a person of this status, sex, and time.",
      "facts": [
        "Fact 1 about grave types (e.g., cist, kurgan).",
        "Fact 2 about common grave goods.",
        "Fact 3 about burial rituals or orientation.",
        "Fact 4...",
        "Fact 5..."
      ]
    }},
    "geographical": {{
      "description": "A narrative describing the local landscape from the individual's perspective.",
      "facts": [
        "Fact 1 about the local flora and fauna of the time.",
        "Fact 2 about the significance of a local river or mountain.",
        "Fact 3...",
        "Fact 4...",
        "Fact 5..."
      ]
    }},
    "historical": {{
      "description": "A description of the major historical events and figures of the era that could have influenced the individual's life.",
      "facts": [
        "Fact 1 about a major regional conflict or the collapse of an empire.",
        "Fact 2 about a powerful neighboring civilization (e.g., Assyria, Hittites).",
        "Fact 3 about a famous ruler or dynasty of the time.",
        "Fact 4...",
        "Fact 5..."
      ]
    }}
  }},
  "occupations": [
    {{
      "role": "Occupation Name 1 (e.g., Elite Warrior)",
      "description": "A single-sentence description of this occupation's duties and social standing."
    }},
    {{
      "role": "Occupation Name 2 (e.g., Potter)",
      "description": "A single-sentence description of this artisan's craft and its importance."
    }},
    {{
      "role": "Occupation Name 3 (e.g., Millet Farmer)",
      "description": "A single-sentence description of this commoner's daily work and contribution to the community."
    }}
  ],
}}

The "occupations" field should contain possible activities/occupations for an individual of the specified sex [SEX] in the given time period and location.
Use the [GEOGRAPHICAL_DESCRIPTION] to ground your response in a specific place, but adapt it to the [GEOGRAPHICAL_DESCRIPTION]. Focus on the specific regional context (e.g., for the Caucasus, discuss Caucasian, Anatolian, and Near Eastern connections, not Vikings)."""


def get_historical_prompt(
    geographical_description: str, time_period: str, sex: str
) -> str:
    """
    Generate a historical analysis prompt for reconstructing an individual's world from the past.

    Args:
        geographical_description (str): A detailed description of a modern location
        time_period (str): The historical period the individual lived in (e.g., 1196-932 calBCE)
        sex (str): The sex of the individual (e.g., female)

    Returns:
        str: Formatted prompt for historical analysis
    """
    return HISTORICAL_PROMPT.format(
        geographical_description=geographical_description,
        time_period=time_period,
        sex=sex,
    )
