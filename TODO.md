# Questions to answer:
1. Should we consider using a browser emulator in order to avoid loading issues for the content.
2. We then need to start pulling information from all sorts of sites in order to start building a training dataset for out model.
   1. This information should include:
      1. All the text content of the webpage
      2. the complete outer html of the webpage
         1. We can use the outer html to try and build a separate robot that is trained to extract information from html content
      3. categorization of the page?
      4. 
3. Workout how to auto label the training data using Inception?...


# Administrative tasks
1. Start building out a manual spreadsheet of 100 properties to consider with their information manually inserted.
2. We can then perform statistical tests on the accuracy of our nlp model vs the manually compiled list of properties
   1. We need to consider what tests we might use (measure)
      1. F-Test?
      2. Accuracy / Recall etc
      3. R^2?

# Locations to check out
1. Liverpool
2. Redhill
3. East London
4. West London
   1. Marylebone
   2. Cross-rail zones
5. Edinburgh
6. Newcastle

## Code Requirements
1. Gauge rental yields from using the rental side of trovit
   1. additionally gauge rental demand by using their api to see interest for each property on the rental side (this info might also be useful on the property search side)
2. 