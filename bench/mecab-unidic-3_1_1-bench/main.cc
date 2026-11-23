#include <mecab.h>

#include <chrono>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace MeCab;

int main(int argc, const char **argv) {
    Tagger *tagger = createTagger("-Owakati -d./resources/unidic-cwj-3.1.1");

    std::vector<std::string> lines;
    for (std::string line; std::getline(std::cin, line);) {
        lines.push_back(line);
    }
    std::vector<char> buf(65536);
    const std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    for (std::string &line : lines) {
        std::strcpy(buf.data(), line.c_str());
        const volatile char *r = tagger->parse(buf.data());
    }
    const std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    const auto d = std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count();
    std::cout << "Elapsed-mecab-unidic-3_1_1: " << static_cast<double>(d) / 1000000 << " [sec]"
              << std::endl;

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if (const char *path = std::getenv("BENCH_TOKENS")) {
        std::ofstream out(path);
        for (std::string &line : lines) {
            std::strcpy(buf.data(), line.c_str());
            for (const Node *node = tagger->parseToNode(buf.data()); node; node = node->next) {
                if (node->stat == MECAB_BOS_NODE || node->stat == MECAB_EOS_NODE) {
                    continue;
                }
                out << std::string(node->surface, node->length) << '\n';
            }
            out << '\n';
        }
    }

    return 0;
}
