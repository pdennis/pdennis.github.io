---
Title: Why Did I Build This Site?
Date: 2022-11-06

---

With all the Elon Musk-inspired Twitter chaos, I've been thinking about a few things: What would I do if Twitter went away? What do I get from Twitter that I would really lose? 

One of the first things that jumped out at me was this: Twitter inspires me to write. Why? My best guess is that it gives me a few things: constant stimulus to get my brain moving, instant feedback, low friction, low stakes. 

At least some parts of that, though, I think could be replicated without Twitter itself. 

So that's what tis blog is. It's low friction, it's low stakes, it provides me with prompts (in the form of a random question at a random time every day). The instant feedback part isn't there yet, and I think that's important, but perhaps by auto-posting to social networks, I'll get there.

## How does this blog work?

Good question. I'm typing it out now, because at the moment, I remember how it works. But that won't last much longer.

### Telegram bot

First, I built a bot with the botfather, and plugged that  into a service called Pipedream, which is a sort of like ifttt for developers. 

### Pipedream

Pipedream takes in the json from the telegram bot, uses jq to strip out just the text of the message and pass it to a variable. It clones the repo for this github pages site, and then formats the text of the message into a post. It then commits its changes back into the repo

### Github pages
The blog itself is based on a template called Chirpy, which conveniently comes with a GitHub action that builds and deploys itself whenever you commit. This is a big timesaver, and the reason I didn't have to code an extra step to deploy. It's pretty nice.
