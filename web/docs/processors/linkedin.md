---
id: linkedin
title: LinkedIn
---

The `LinkedIn` provider includes processors that can use your LinkedIn account and perform various actions like retrieving profile activity of your connections etc.

## Profile Activity

### Input

- `profile_url`: The LinkedIn profile URL of the person whose activity you want to retrieve.
- `search_term`: The search term to use when looking for a user when profile url is unavailable.

### Configuration

- `connection_id`: The connection ID of the LinkedIn account to use. Add a connection of type `Web Login` from Settings > Connections (and login to your LinkedIn account from the remote web browser).
- `n_posts`: The maximum number of posts to retrieve.
- `n_comments`: The maximum number of comments to retrieve.
- `n_reactions`: The maximum number of reactions to retrieve.

### Output

- `posts`: A list of posts.
- `comments`: A list of comments.
- `reactions`: A list of reactions.
- `profile_url`: The LinkedIn profile URL of the person whose activity was retrieved.
- `error`: An error message if something went wrong.
