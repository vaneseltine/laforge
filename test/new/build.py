import pathlib
import laforge.decoupage as lf


@lf.read("small", "../samples/small.csv")
def read_in_data(small):
    print(small)


read_in_data()

# templated_content = self.template_content(raw_content, section_config)
# task = Task.from_strings(
#     raw_verb=option,
#     raw_content=templated_content,
#     config=section_config,
# )
# logger.debug(task)
