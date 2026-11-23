#include <kytea/kytea.h>
#include <kytea/kytea-struct.h>
#include <kytea/string-util.h>

#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>

using namespace kytea;

int main(int argc, const char **argv) {
    KyteaConfig *config = new KyteaConfig;
    config->setDebug(0);
    config->setOnTraining(false);
    config->parseRunCommandLine(argc, argv);

    Kytea *kytea = new Kytea(config);

    kytea->readModel(config->getModelFile().c_str());
    StringUtil *util = kytea->getStringUtil();

    int n_words = 0;
    std::vector<std::string> lines;
    for (std::string line; std::getline(std::cin, line);) {
        lines.push_back(line);
    }
    const std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    for (std::string line : lines) {
        const KyteaString surface_string = util->mapString(line);
        KyteaSentence sentence(surface_string, surface_string);
        kytea->calculateWS(sentence);
        n_words += sentence.words.size();
    }
    const std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    const auto d = std::chrono::duration_cast<std::chrono::microseconds>(end - begin).count();
    std::cout
        << "Elapsed-kytea: "
        << static_cast<double>(d) / 1000000
        << " [sec]" << std::endl;
    std::cerr << n_words << std::endl;

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if (const char *path = std::getenv("BENCH_TOKENS")) {
        std::ofstream out(path);
        for (const std::string &line : lines) {
            const KyteaString surface_string = util->mapString(line);
            KyteaSentence sentence(surface_string, surface_string);
            kytea->calculateWS(sentence);
            for (const KyteaWord &word : sentence.words) {
                out << util->showString(word.surface) << '\n';
            }
            out << '\n';
        }
    }

    return 0;
}
