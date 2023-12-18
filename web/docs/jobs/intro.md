---
id: introduction
title: Jobs
---

You can use jobs to run your apps with a batch of inputs. Jobs are useful when you want to run your app with a large number of inputs. For example, you might want to run your app with a list of leads to send emails to, or a list of documents to summarize, or a list of documents to extract entities from etc. You can create a job with a list of inputs and run your app with the job. LLMStack will run your app with each input in the job and return the results as a CSV file.

![Jobs](/img/ui/jobs.png)

There are three types of jobs:

### Single Run

These are one time jobs that run your app with a list of inputs and return the results as a CSV file. You can download the results from the UI or from the API.

### Recurring

These are recurring jobs that run your app with a list of inputs at a specified interval for a specified number of times and return the results as a CSV file for each run.

### Cron

These are cron jobs that run your app with a list of inputs at a specified interval and return the results as a CSV file for each run.
