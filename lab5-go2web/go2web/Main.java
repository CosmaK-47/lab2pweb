package go2web;

public class Main {

  public static void showHelp() {
    System.out.println(
      "Usage:\n" +
        "  go2web -u <URL>         Make an HTTP request to the specified URL\n" +
        "  go2web -s <search-term> Search the term using a search engine\n" +
        "  go2web -h               Show this help\n"
    );
  }

  public static void main(String[] args) {

    if (args.length == 0) {
      showHelp();
      return;
    }

    switch (args[0]) {

      case "-h":
        showHelp();
        break;

      case "-u":
        if (args.length < 2) {
          System.out.println("Error: URL missing");
          return;
        }
        System.out.println("CLI received URL request:");
        System.out.println("URL = " + args[1]);
        break;

      case "-s":
        if (args.length < 2) {
          System.out.println("Error: search term missing");
          return;
        }

        StringBuilder term = new StringBuilder();
        for (int i = 1; i < args.length; i++) {
          term.append(args[i]).append(" ");
        }

        System.out.println("CLI received search request:");
        System.out.println("Query = " + term.toString().trim());
        break;

      default:
        System.out.println("Unknown command");
        showHelp();
    }
  }
}
