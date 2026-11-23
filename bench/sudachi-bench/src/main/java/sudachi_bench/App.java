package sudachi_bench;

import java.io.IOException;
import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import com.worksap.nlp.sudachi.Tokenizer;
import com.worksap.nlp.sudachi.Dictionary;
import com.worksap.nlp.sudachi.DictionaryFactory;
import com.worksap.nlp.sudachi.Morpheme;
import java.util.List;
import java.util.ArrayList;
import java.util.Scanner;
import java.time.Instant;
import java.time.Duration;
import java.nio.file.Paths;
import java.nio.file.Files;

public class App {
    public static void main(String[] args) throws IOException {
        // The split mode from the first argument (A, B or C; C when it is left
        // out). valueOf stops on anything else.
        Tokenizer.SplitMode mode = Tokenizer.SplitMode.valueOf(args.length > 0 ? args[0] : "C");
        String series = "sudachi-" + mode.name().toLowerCase();
        String settings = Files.readString(Paths.get("sudachi.json"));
        Scanner input = new Scanner(System.in, "utf-8");
        List<String> lines = new ArrayList<String>();
        while (input.hasNext()) {
            lines.add(input.nextLine());
        }
        try (Dictionary dict = new DictionaryFactory().create(settings)) {
            Tokenizer tokenizer = dict.create();
            int n_words = 0;
            Instant start = Instant.now();
            for (String line : lines) {
                List<Morpheme> tokens = tokenizer.tokenize(mode, line);
                n_words += tokens.size();
            }
            Instant finish = Instant.now();
            double timeElapsed = (double) Duration.between(start, finish).toNanos() / 1000000000;
            System.out.println("Elapsed-" + series + ": " + timeElapsed + " [sec]");
            System.out.println(n_words);

            // With BENCH_TOKENS=<file>, write the tokens of every line after
            // the timed loop, one per line with an empty line after each input
            // line, for segmentation.py. The timed loop above is unchanged.
            String path = System.getenv("BENCH_TOKENS");
            if (path != null) {
                try (BufferedWriter out = Files.newBufferedWriter(Paths.get(path), StandardCharsets.UTF_8)) {
                    for (String line : lines) {
                        // Sudachi can give a morpheme an empty surface (inside
                        // "……", for example); it covers no text, and an empty
                        // line would end the line's tokens, so it is not written.
                        for (Morpheme morpheme : tokenizer.tokenize(mode, line)) {
                            if (!morpheme.surface().isEmpty()) {
                                out.write(morpheme.surface());
                                out.write('\n');
                            }
                        }
                        out.write('\n');
                    }
                }
            }
        }
    }
}
