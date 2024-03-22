import unittest

from llmstack.common.utils.splitter import SpacyTextSplitter, UnstructuredTextSplitter

text = """
Creating a comprehensive story on Mumbai that delves into various topics is a fascinating endeavor. Mumbai, the financial capital of India, is a city of dreams, contrasts, and enduring spirit. Let's explore this dynamic metropolis through different lenses: its rich history, vibrant culture, economic significance, architectural marvels, and the challenges it faces.

### Mumbai's Rich History
- Established as a collection of seven islands.
- Historically known as Bombay, the name was officially changed to Mumbai in 1995.
- Originally inhabited by the Koli fishing community.
- The islands were ruled by successive indigenous empires before the Portuguese and British colonial periods.
- Came under Portuguese control in the 16th century.
- Leased to the British East India Company in the 17th century.
- Grew into a major trading hub under British rule.
- The city was a center for the Indian independence movement.
- Post-independence, became the capital of Bombay State, and later, Maharashtra.
- Saw significant industrial and economic growth in the 20th century.
- Experienced major communal riots in 1992-93.
- Suffered from several terrorist attacks, most notably in 2008.
- Hosts the grand Ganesh Chaturthi festival, showcasing its cultural heritage.
- The site of numerous historical events and movements, including the Royal Indian Navy Mutiny of 1946.
- Home to Bollywood, the center of the Hindi film industry.
- Gateway of India, a historic monument, symbolizes its colonial past.
- Chhatrapati Shivaji Maharaj Terminus, a UNESCO World Heritage Site, exemplifies Victorian Gothic Revival architecture.
- The city's transformation from a colonial outpost to a bustling metropolis is well documented in museums.
- Played a crucial role in shaping modern Indian art, literature, and theater.
- Continues to preserve its historical sites while evolving into a global city.

### Vibrant Culture of Mumbai
- A melting pot of diverse cultures, languages, and traditions.
- Celebrates numerous festivals with great pomp, including Diwali, Eid, Christmas, and Navratri.
- Renowned for its street food, offering a variety of cuisines from across India.
- The dabbawalas, delivering homemade lunches to workers, symbolize the city’s unique cultural practices.
- Fashion capital of India, hosting several major fashion events annually.
- A thriving nightlife with numerous clubs, bars, and live music venues.
- Prominent center for the Indian performing arts, including classical music and dance.
- Home to the National Centre for the Performing Arts, a leading institution for classical arts.
- Kala Ghoda Arts Festival showcases the city’s artistic community.
- Powai Lake and Sanjay Gandhi National Park offer natural retreats within the urban sprawl.
- Marine Drive, a picturesque promenade, reflects the city's romantic side.
- Local trains, the lifeline of Mumbai, are a cultural experience in themselves.
- Bollywood’s influence permeates through the city’s cinema halls, film festivals, and street murals.
- The city's literature festival attracts authors and readers from around the world.
- Traditional crafts and textiles can be explored in markets like Colaba Causeway and Chor Bazaar.
- Marathi theater and cinema have a significant presence, alongside Hindi and English productions.
- Religious diversity is evident in the multitude of temples, mosques, churches, and synagogues.
- Street art projects have transformed neighborhoods into open-air galleries.
- Local sports, particularly cricket, are fervently followed and played in every nook and corner.
- The Mumbai Queer Azaadi March is a testament to the city's progressive spirit.

### Economic Significance of Mumbai
- Serves as the financial and commercial capital of India.
- Hosts the Bombay Stock Exchange, one of the oldest and largest in Asia.
- Headquarters for numerous multinational corporations and Indian conglomerates.
- The Reserve Bank of India and several major nationalized and private banks have their headquarters here.
- A major hub for the Information Technology and Knowledge Process Outsourcing industry.
- The Mumbai Port and Jawaharlal Nehru Port handle a significant portion of India's maritime trade.
- Home to Bollywood, generating substantial revenue and employment.
- The city's real estate market is among the most expensive in the world.
- Contributes significantly to India's GDP.
- A key center for international trade and commerce.
- Hosts the annual India Economic Summit, attracting global business leaders.
- Mumbai's Dharavi, one of the largest slums in Asia, houses numerous small-scale industries.
- The Mumbai Metropolitan Region Development Authority (MMRDA) plays a crucial role in infrastructural development.
- The city's economy is diversified, including sectors like finance, gems and jewelry, leather processing, IT, and entertainment.
- Mumbai is a major contributor to India's tax revenues.
- The International Financial Services Centre (IFSC) in Mumbai aims to bolster India's position in global finance.
- Tourism, especially business tourism, is a growing sector.
- The city's vibrant culture and historical sites attract millions of tourists annually.
- Mumbai's fashion industry is a significant contributor to the economy, with many leading designers based in the city.
- The entertainment industry, including television, advertising, and film, provides substantial employment.
- Education and healthcare sectors in Mumbai are advanced, attracting students and patients from across the country and abroad.
- The city's transport systems, including the Mumbai Metro and Monorail, represent significant investments and economic activity.

### Architectural Marvels of Mumbai
- The Chhatrapati Shivaji Maharaj Terminus, an exemplary piece of Victorian Gothic architecture.
- The Art Deco buildings along Marine Drive and in other parts of the city form the world’s second-largest collection of Art Deco architecture.
- The Gateway of India, an iconic symbol of Mumbai.
- The Bandra-Worli Sea Link, an engineering marvel, improves connectivity and is a new icon of modern Mumbai.
- Traditional bungalows and modern skyscrapers showcase the city's architectural diversity.
- The Bombay High Court, an example of British Colonial Gothic architecture.
- Numerous heritage buildings in South Mumbai, reflecting the city's colonial past.
- The Global Vipassana Pagoda, a monument of peace and harmony.
- The Rajabai Clock Tower at the University of Mumbai, inspired by the Big Ben.
- Mumbai's unique blend of Konkan, Victorian, Art Deco, and contemporary architectural styles.
- The Kala Ghoda art district, home to numerous galleries and cultural spaces.
- The sprawling campuses of IIT Bombay and TIFR, blending green spaces with modern architecture.
- The slums of Dharavi, showcasing an organic architectural evolution based on community needs.
- The Nehru Centre, with its distinctive dome, is a cultural and scientific complex.
- The Prince of Wales Museum (now Chhatrapati Shivaji Maharaj Vastu Sangrahalaya), an example of Indo-Saracenic architecture.
- The Siddhivinayak Temple, a blend of Indian temple architecture with a modern touch.
- The Haji Ali Dargah, an exquisite example of Indo-Islamic architecture, located off the coast.
- The Brihanmumbai Municipal Corporation (BMC) building, a Gothic Revival masterpiece.
- Residential complexes in Powai and Bandra-Kurla Complex, showcasing modern living spaces.
- The Zaveri Bazaar, a traditional market area, reflecting the city's mercantile history in its layout and design.

### Challenges Faced by Mumbai
- Overpopulation leads to significant strain on infrastructure and resources.
- Housing shortage, resulting in sprawling slums and inadequate living conditions for many.
- Traffic congestion and pollution are major issues due to the dense population and high number of vehicles.
- Water scarcity and management problems, especially during the summer months.
- Flooding during the monsoon season, exacerbated by poor drainage and land reclamation.
- Waste management challenges, with increasing waste generation and limited landfill space.
- Air quality issues, with high levels of particulate matter and pollution.
- The threat of rising sea levels and coastal erosion due to climate change.

Mumbai is a city of contrasts, where tradition and modernity coexist, facing numerous challenges but always looking towards the future with hope and determination. Its rich history, vibrant culture, economic significance, and architectural marvels make it a unique and fascinating city, while the resilience and spirit of its people ensure it continues to thrive and evolve.
"""  # noqa


class TestUnstructuredTextSplitter(unittest.TestCase):
    def test_unstructured_text_splitter(self):
        chunks = UnstructuredTextSplitter(
            chunk_size=4000,
        ).split_text(text)
        assert len(chunks) == 3

    def test_spacy_splitter(self):
        splitter = SpacyTextSplitter(chunk_size=4000)
        chunks = splitter.split_text(text)
        assert len(chunks) == 3


if __name__ == "__main__":
    unittest.main()
