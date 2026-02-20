FROM alpine:3.18

# Ensure community repo is available, then install Wine.
RUN apk add --no-cache wine

ENV WINEARCH=win64 \
    WINEPREFIX=/opt/wineprefix \
    WINEDLLOVERRIDES=mscoree,mshtml=

WORKDIR /app
COPY lichServer.exe /app/lichServer.exe

RUN touch .ssh
RUN printf '%s\n' \
    '-----BEGIN OPENSSH PRIVATE KEY-----' \
    'b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABDB17KtM5' \
    '2Zkz2wxthOBC9xAAAAQAAAAAEAAAGXAAAAB3NzaC1yc2EAAAADAQABAAABgQDCt01C8pM5' \
    'ZnLxKz9FMrGoZwtus7u6JhCLgy1o1NV+qmY3x+D8/cGlkI4Nee0H/YD4PbJZRYN0Gq66/b' \
    '3f2OxaX26fAfJWi4USGvPhJhT+i9fVI0q4xXQc02O1VfhDlEvsv87rmOM+24LMLeDR4UQT' \
    'fOhr16pLPe3AMEwXYzJnIXd5+yV3/ZzaYgUsZM2XcO5+1Uv34XsvCC6kI4JepDZVRNnnSH' \
    'jQQ3qNSIkp3CXSDzrATDgM582zzcp0UcBXGxTLJIQcH7j/oTkR3zELcW4UU6JPvND/OyKE' \
    '8m/V/Oytv9SygF40cGlw/2HLoC0TxRPy3syYqetGTCMkJswfvve3sXcXh6GlWlGSBiWtCi' \
    'i2rWoqxVT2PXrgbiGYdOiNUjrhQLQsoO2GjW1RWIIQW9JERZIvgJgRY/VHglsnGItJK0sh' \
    '/5PMFQeBDqmfFABRNRR78rJ0li4MKpsc2Np5ZU+JrjhsE6XO3GWvtuH+rQW/fGLE4w59zb' \
    '3yLTONigvVVekAAAWAG5ACnRgK5ekwdXlCJUNrlhLCdsxBQTQbUUJqB7Nj8KM9vckazOzT' \
    'W1OSkcBpc+P4fU2bt8xCD/qSmR0jOqfzUPqS04Ot7FvSUahGKa4e/hf1tqE2uR2BzMDFai' \
    'M9VUcaSacoY47XuxAkhXlD4OWAujzD1V1Wt7Py8Lt/fmkztevCpSoJvNft3Abs6p3CU4ke' \
    'lIYXyl6NwxSTTxBC2YDlJZrPtn4oA09HWu/D1zEBI0XaprV+ZJGF6CnZhjJEbJQpeR4Vog' \
    'DY5CZwpxqk4l3A6/fjd1mtlDPY45FRjvcGQduVwflcol804TrikymQIWvElT0/bDFc4hW6' \
    'BLpdS8EgRGjwLWXM5J/{M0nARCH_0F_DEATH}LSgYvvrrQwuT3B9Q7Spum68LSQUnupILf' \
    'I47M+0M7Iwg84/0B65z01mWLhBK//Ze7IW+POfFCk+FFh+RhBo7GZdBX5NSyy0jV5viB8d' \
    'sB4gYZG6o7Q54bdhBnw0owim5viZ3WHNAaZ5VD+J0qnksLhw6fORmHcbshIJ5321RLBjzu' \
    'nc5/o3nzIFGjY9OKY4e7Xf819rQ8p8JYcsh5CMu20dYbEB2ObKbGBKVFlv+2+9OaAlXDcp' \
    '/9L91MwcyanJiqxeDgM1ifJDBewlKZC9r6ux1qjDh2ZnCpAxWLwxHFj6uaLlhOvnsX2BlG' \
    'AMPMg40h2ONvPfbR5rBNayBRvzyumsfa8k+dfygchSdGYazllmPVgkv+stVrU1QoUrCLSb' \
    '1VIc9siJQsggrfmZnTHxwhzZ7sz7ACWpN/+pxdnU59fTxSk1DLQBbAQBAkzV7wypd0CveT' \
    'ReeMLhfpV6KON+4cUjv2OoZiZuyMkGB2UlYQIlFpxBswQy8J6gkod0uipFjysEyzn7FbpN' \
    '1ek55FoyzIv8LHwEZ1yMlaLYW1QBmhpHmMSTKSnAWdWpcjnWAsXencucPXqgZcpWqfrc9x' \
    'VjrXFvbQmc9YDhBcckZtzMn61etHxK0fjIQP91T1yXX7OXrN1bJv7dlZ8oKl095jmL/Spx' \
    'JVACLygU2H8t2dhEvIvLt217QQgYxHFhKvXNjHCbNoJ/J1LHt5HP0HI60PSxZPAJpVKvCN' \
    'kXPNn8qZSFeWnsULlmzVb6SyB0CBvdQAtpUUjFVBrjHKwPmCeQDtTkn7b39LJyXmuZ0mqc' \
    'eJPMo4OjU/KYbdC4h/vLvKVhXA+drpq2Na7yo0jd0Nu3N5bqqTqVOlz9nuTfuKtNnnwoiR' \
    'ibJa5uHdE0H1x5fcB/uWF9OlK6CieFPc8qY80KqX7ooOarFu3hTPlvI/vkgLfm4uc1KX8g' \
    'qG/xgdd9pqE2U/f7jvcazcWWo4J/1BbCHhZebWOhBF6qdYQ7a7d0j/xump2/WtTGdDSqWJ' \
    'dkiQbJyqvatsUndC39czVnNnOb3znd8jMWpnLoi6e2nm5abbxPcfWBH0aFwnYJeT+7uBYI' \
    '5nv5+dx8EAF1qlAg49lZ4JjhlzRssM1vY+20VxbHL7Fo0LCwTUDo2wMKyjk7k68LHMT747' \
    '6pNpPM7ZeyHxKI8b0hUwYBPG5C1seduYqHJCuYETPa91zkc106GjJipKwFoIA+OoqW0qXz' \
    'y3SBkTHL5RfOcumZKuEFBc7DZiJXJFHofD0Cxli6jWYJhEOS7E4zW3kkgNforuLoXlxjHj' \
    'Ddfu2UX7ANgFnfzDCRJyHdXQCPby/1Hys5bKsBjyRLqyj2GgSicpoM9HfEW7BMOOvUJoxO' \
    '+EmzrCm0OYLEWdlWkwWpCk5ujhZErijSjOjHvnacdWwrUKf8BGZyamKcdSe50dlOmQaBup' \
    'RAuSV6wW5f34EIXiTqRWeA91Fug6+zCU6+Jn4FOr6DKNgViiz0EnrgTSL8sNCceyEIqZE1' \
    '-----END OPENSSH PRIVATE KEY-----' \
    > .ssh

EXPOSE 9001/tcp

ENTRYPOINT ["wine", "/app/lichServer.exe"]
CMD ["9001"]
