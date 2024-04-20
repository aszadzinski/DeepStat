from conf import tex_config
from manager import Analysis

if __name__ == "__main__":
    analysis = Analysis(tex_config, compile=True)
    analysis.register_commands()
    analysis.create_table_of_content()
    analysis.boost_commands()
    analysis.build_document()

    #df = data_loader("data/data.xlsx")
    #data = generate_metric(df)
