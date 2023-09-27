import unittest

from llmstack.common.utils.splitter import CSVTextSplitter, CharacterTextSplitter

# Unitest for CSVTextSplitter


class TestCSVTextSplitter(unittest.TestCase):
    def test_csv_splitter(self):
        csv_data = """
        a,b,c,d,e
        1,2,3,4,"Foo"
        5,6,7,8,"Bar"
        9,10,11,12,"Baz"
        """
        output = CSVTextSplitter(
            chunk_size=100, chunk_overlap=1,
            length_function=CSVTextSplitter.num_tokens_from_string_using_tiktoken,
        ).split_text(csv_data)
        print(len(output))

class TestCharacterTextSplitter(unittest.TestCase):
    def test_character_split(self):
        text_data = """ 
        Mumbai is built on what was once an archipelago of seven islands: Isle of Bombay, Parel, Mazagaon, Mahim, Colaba, Worli, and Old Woman's Island (also known as Little Colaba).[63] It is not exactly known when these islands were first inhabited. Pleistocene sediments found along the coastal areas around Kandivali in northern Mumbai suggest that the islands were inhabited since the South Asian Stone Age.[64] Perhaps at the beginning of the Common Era, or possibly earlier, they came to be occupied by the Koli fishing community.[65][66]

        In the 3rd century BCE, the islands formed part of the Maurya Empire, during its expansion in the south, ruled by the Buddhist emperor Ashoka of Magadha.[67] The Kanheri Caves in Borivali were excavated from basalt rock in the first century CE,[68] and served as an important centre of Buddhism in Western India during ancient Times.[69] The city then was known as Heptanesia (Ancient Greek: A Cluster of Seven Islands) to the Greek geographer Ptolemy in 150 CE.[70] The Mahakali Caves in Andheri were cut out between the 1st century BCE and the 6th century CE.[71][72]
        """
        output = CharacterTextSplitter(
            separator='.', is_regex=False, 
            chunk_size=100, chunk_overlap=0,
        ).split_text(text_data)
        
        print(output)
    
if __name__ == '__main__':
    unittest.main()