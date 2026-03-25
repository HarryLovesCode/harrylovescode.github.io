---
date: 3-24-2026
tags:
  - Update
---

# A Little Update

Life has been busy. In one year, I got married and bought my first home. Given all the change, I figured I would take some time to reflect on some things that have been on my mind.

## No Place Like (my) 127.0.0.1-lab

I have realized in the transition from someone else's house to my own house, that ownership is one thing I really value. With the rising costs of memory, I almost feel responsible to keep that in mind.

In a world where everyone and their mom is shipping Electron apps (and I do not want to hate on this, I love Electron and Tauri), we have to find some balance. We want a good developer experience, but also a good user experience. In my career, these are hard to balance -- if not impossible.

This leads me to the main thing on my mind, (pardon my french) the enshittification of modern SaaS applications for the sake of prioritizing AI development.

My stance on AI is abundantly clear: I love it as a tool, not a crutch. When that crutch drives a wedge between a tool built by developers for developers, I will drag my feet, but ultimately accept that I need to move on to a different tool.

The last outgoing tool was Windows 11, now, it's Github.

## Your IP (Intellectual Property), Your IP (Address)

Barring the drama with [Gitea](https://about.gitea.com/) and the hard-fork with [Forgejo](https://forgejo.org/), this is absurdly refreshing. I pull up the list of repositories I have, the bottom of the page reads: 

> Powered by Gitea
Version: 1.25.4 Page: 5ms Template: 3ms

Not seconds, milliseconds. I would joke "the way it should be", but I would never expect that of Github. That said, I would expect that the *client-side navigation* would not take so long. Beyond feeling extremely snappy, it is minimal, has only distractions introduced by *you*, and feels mostly on-par feature parity-wise. All that, and it runs in a very small footprint. That page was rendered on my Raspberry Pi 5. Go with a lightweight HTTP server and template-based rendering does a number on your response time.

Now, why Git as the example for this? Well, other than Nvidia, there is only one company that I think has a chance of benefiting substantially from the AI gold-rush, Github's parent company Microsoft. Now, call me paranoid, but I am not worried about what I put out *publicly* and open-source becoming fair-grounds for training. I am worried about my private repositories being used as training data. From notes to POCs, big-ideas to hacky garbage, I produce a lot of code both good and bad. And, at the end of the day, I want a version control of my brain.

Do I think every developer should self-host Git? No, quite frankly I don't. In fact, I have come to accept not every developer shares the same passion for homelab that I do. Nor, do they build software outside of work.

## Back to Resources

So there is the context, now onto my current arc of niche programming. Building a small SSG for my blog was fun and all, but a statically rendered blog only gets you so far. These are the things I want to explore:

Frameworks:

- [htmx](https://htmx.org/) - I have been using this on-and-off for a few months. I am by no means a die-hard fan, I think I have come to a realization that while JQuery was not the move all those years ago, neither is Next.js. A bigger tool is not always a better one and that applies to both.
- [alpine.js](https://alpinejs.dev/) - This compliments htmx rather well. HTMX is the server-side glue, alpine.js is the client-side version. This with Tailwind and [Hono](https://hono.dev/) feel like an eclectic match made in heaven. But what I think I like most about this setup, is any language with a web server and templating library can render server-side with high throughput and a minimal footprint.

The resources were the initial focus, but they got lost in the tangent. Because the only different between where we are and where we could be just a matter of perspective. My perspective is, I yearn for simplicity. Some tech-stack I *enjoy* working with that produces applications that users will have a good experience with that have a decent UI. Because while a lot of SaaS apps focus on the very last, the first two are all that matters to me.

While I cannot control it at work, I take pride in owning my resources at home. Not someone else's cloud. I learn to deploy, I learn to manage, I grow as a developer and I find things that reignite my excitement for programming. That is my little update while I wait for the dry-wall patch to dry. Behind that patch is Cat6a so expect some homelab updates.

Until next time, cheers.