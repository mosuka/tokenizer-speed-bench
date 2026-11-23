package kuromoji_bench;

import com.atilika.kuromoji.ipadic.Token;
import com.atilika.kuromoji.ipadic.Tokenizer;
import java.util.List;
import java.util.ArrayList;
import java.util.Scanner;
import java.time.Instant;
import java.time.Duration;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

public class App {
    public static void main(String[] args) throws IOException {
        Tokenizer tokenizer = new Tokenizer();
        Scanner input = new Scanner(System.in, "utf-8");
        List<String> lines = new ArrayList<String>();
        while (input.hasNext()) {
            lines.add(input.nextLine());
        }
        Instant start = Instant.now();
        int n_words = 0;
        for (String line : lines) {
            List<Token> tokens = tokenizer.tokenize(line);
            n_words += tokens.size();
        }
        Instant finish = Instant.now();
        double timeElapsed = (double) Duration.between(start, finish).toNanos() / 1000000000;
        System.out.println("Elapsed-kuromoji: " + timeElapsed + " [sec]");
        System.out.println(n_words);

        // With BENCH_TOKENS=<file>, write the tokens of every line after the
        // timed loop, one per line with an empty line after each input line,
        // for segmentation.py. The timed loop above is unchanged.
        String path = System.getenv("BENCH_TOKENS");
        if (path != null) {
            try (BufferedWriter out = Files.newBufferedWriter(Paths.get(path), StandardCharsets.UTF_8)) {
                for (String line : lines) {
                    for (Token token : tokenizer.tokenize(line)) {
                        out.write(token.getSurface());
                        out.write('\n');
                    }
                    out.write('\n');
                }
            }
        }
    }
}
