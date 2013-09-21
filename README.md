# civic-json-worker

[Flask](http://flask.pocoo.org) app for tracking opengov projects in Chicago.

## Objective

Keep track of all the civic tech projects worked on at the Chicago open gov hack night. Eventually this could track all civic projects in Chicago, or even nationally.

## The plan

Curate a simple list of Github URLs for civic tech projects and leave filling in the rest to the [Github API](http://developer.github.com/). 

Looking at [other civic tech listing projects](http://commons.codeforamerica.org/) like this that have [gone stale](http://digital.cityofchicago.org/index.php/open-data-applications/), the real sticking point is in maintaining and curating the list of projects. If we can make the maintenance part as simple as possible, we have a greater chance that this thing will live on.

So humans will be responsible for one thing: __deciding what gets tracked__. 

```json
[
    "https://github.com/dssg/census-communities-usa",
    "https://github.com/open-city/open-gov-hack-night",
    ...
]
```

The rest is up to computers. When the ``/update-projects/`` path is hit on this app, it loops over the projects in the list and captures something like this:

``` json
* title
* description
* website URL (if any)
* contributors (list of people)
* programming language
* how active / last updated
* number of stars/forks
* number of issues?
```

This data itself will be served up by the worker as its own JSON file, for [use on this site](http://opengovhacknight.org/projects.html) for listing/sorting/searching projects. __bonus:__ anyone will be able to use this JSON file for their own purposes. Take a look at [Microjs.com](http://microjs.com/#) as an example of this.

Also, we could easily create a submit form so anyone can submit a Github URL to this list.

## Benefits

By pushing everything on to Github, we will have very little to maintain, content-wise, as administrators. Simultaneously, we will encourage people to:

* sign up for Github if they aren't already
* keep their projects open source (we can't crawl private repos)
* make sure their description and website urls are up to date
* use the issue tracker

## Feedback

@ryanbriones, this derives from the [civic.json](https://github.com/ryanbriones/civicneeds/issues/4) that has been discussed with @robdodson. Any thoughts? @GovInTrenches?


