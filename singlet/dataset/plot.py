# vim: fdm=indent
# author:     Fabio Zanini
# date:       16/08/17
# content:    Dataset functions to plot gene expression and phenotypes
# Modules
import warnings
import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib import cm

from .plugins import Plugin
from ..config import config


try:
    import seaborn as sns
except (ImportError, RuntimeError):
    if 'seaborn_import' not in config['_once_warnings']:
        warnings.warn('Unable to import seaborn: plotting will not work')
        config['_once_warnings'].append('seaborn_import')
    sns = None

try:
    import matplotlib.pyplot as plt
except (ImportError, RuntimeError):
    if 'pyplot_import' not in config['_once_warnings']:
        warnings.warn('Unable to import matplotlib.pyplot: plotting will not work')
        config['_once_warnings'].append('pyplot_import')
    plt = None


# Classes / functions
class Plot(Plugin):
    '''Plot gene expression and phenotype in single cells'''

    @staticmethod
    def _update_properties(kwargs, defaults):
        Plot._sanitize_plot_properties(kwargs)
        Plot._sanitize_plot_properties(defaults)
        for key, val in defaults.items():
            if key not in kwargs:
                kwargs[key] = val

    @staticmethod
    def _sanitize_plot_properties(kwargs):
        aliases = {
                'linewidth': 'lw',
                'antialiased': 'aa',
                'color': 'c',
                'linestyle': 'ls',
                'markeredgecolor': 'mec',
                'markeredgewidth': 'mew',
                'markerfacecolor': 'mfc',
                'markerfacecoloralt': 'mfcalt',
                'markersize': 'ms',
                }
        for key, alias in aliases.items():
            if alias in kwargs:
                kwargs[key] = kwargs.pop(alias)

    def plot_coverage(
            self,
            features='total',
            kind='cumulative',
            ax=None,
            tight_layout=True,
            legend=False,
            **kwargs):
        '''Plot number of reads for each sample

        Args:
            features (list or string): Features to sum over. The string \
                    'total' means all features including spikeins and other, \
                    'mapped' means all features excluding spikeins and other, \
                    'spikeins' means only spikeins, and 'other' means only \
                    'other' features.
            kind (string): Kind of plot (default: cumulative distribution).
            ax (matplotlib.axes.Axes): The axes to plot into. If None \
                    (default), a new figure with one axes is created. ax must \
                    not strictly be a matplotlib class, but it must have \
                    common methods such as 'plot' and 'set'.
            tight_layout (bool or dict): Whether to call \
                    matplotlib.pyplot.tight_layout at the end of the \
                    plotting. If it is a dict, pass it unpacked to that \
                    function.
            legend (bool or dict): If True, call ax.legend(). If a dict, \
                    pass as **kwargs to ax.legend.
            **kwargs: named arguments passed to the plot function.

        Returns:
            matplotlib.axes.Axes with the axes contaiing the plot.
        '''

        if ax is None:
            new_axes = True
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(13, 8))
        else:
            new_axes = False

        defaults = {
                'linewidth': 2,
                'color': 'darkgrey',
                }
        Plot._update_properties(kwargs, defaults)

        counts = self.dataset.counts
        if features == 'total':
            pass
        elif features == 'mapped':
            counts = counts.exclude_features(spikeins=True, other=True)
        elif features == 'spikeins':
            counts = counts.get_spikeins()
        elif features == 'other':
            counts = counts.get_other_features()
        else:
            counts = counts.loc[features]

        if kind == 'cumulative':
            x = counts.values.sum(axis=0)
            x.sort()
            y = 1.0 - np.linspace(0, 1, len(x))
            ax.plot(x, y, **kwargs)
            ax_props = {
                    'ylim': (-0.05, 1.05),
                    'ylabel': 'Cumulative distribution'}
        else:
            raise ValueError('Plot kind not understood')

        if not counts._normalized:
            ax_props['xlabel'] = 'Number of reads'
        elif counts._normalized != 'custom':
            ax_props['xlabel'] = counts._normalized.capitalize().replace('_', ' ')

        if new_axes:
            xmin = 0.5
            xmax = 1.05 * x.max()
            ax_props['xlim'] = (xmin, xmax)
            ax_props['xscale'] = 'log'
            ax.grid(True)

        ax.set(**ax_props)

        if legend:
            if np.isscalar(legend):
                ax.legend()
            else:
                ax.legend(**legend)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

        return ax

    def scatter_statistics(
            self,
            features='mapped',
            x='mean',
            y='cv',
            ax=None,
            tight_layout=True,
            legend=False,
            grid=None,
            **kwargs):
        '''Scatter plot statistics of features.

        Args:
            features (list or string): List of features to plot. The string \
                    'mapped' means everything excluding spikeins and other, \
                    'all' means everything including spikeins and other.
            x (string): Statistics to plot on the x axis.
            y (string): Statistics to plot on the y axis.
            ax (matplotlib.axes.Axes): The axes to plot into. If None \
                    (default), a new figure with one axes is created. ax must \
                    not strictly be a matplotlib class, but it must have \
                    common methods such as 'plot' and 'set'.
            tight_layout (bool or dict): Whether to call \
                    matplotlib.pyplot.tight_layout at the end of the \
                    plotting. If it is a dict, pass it unpacked to that \
                    function.
            legend (bool or dict): If True, call ax.legend(). If a dict, \
                    pass as **kwargs to ax.legend.
            grid (bool or None): Whether to add a grid to the plot. None \
                    defaults to your existing settings.
            **kwargs: named arguments passed to the plot function.

        Returns:
            matplotlib.axes.Axes with the axes contaiing the plot.
        '''
        if ax is None:
            new_axes = True
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(13, 8))
        else:
            new_axes = False

        defaults = {
                's': 10,
                'color': 'darkgrey',
                }
        Plot._update_properties(kwargs, defaults)

        counts = self.dataset.counts
        if features == 'total':
            if not counts._otherfeatures.isin(counts.index).all():
                raise ValueError('Other features not found in counts')
            if not counts._spikeins.isin(counts.index).all():
                raise ValueError('Spike-ins not found in counts')
            pass
        elif features == 'mapped':
            counts = counts.exclude_features(
                    spikeins=True, other=True,
                    errors='ignore')
        else:
            counts = counts.loc[features]

        stats = counts.get_statistics(metrics=(x, y))
        ax_props = {'xlabel': x, 'ylabel': y}
        x = stats.loc[:, x]
        y = stats.loc[:, y]

        ax.scatter(x, y, **kwargs)

        if ax_props['xlabel'] == 'mean':
            xmin = 0.5
            xmax = 1.05 * x.max()
            ax_props['xlim'] = (xmin, xmax)
            ax_props['xscale'] = 'log'
        elif ax_props['ylabel'] == 'mean':
            ymin = 0.5
            ymax = 1.05 * y.max()
            ax_props['ylim'] = (ymin, ymax)
            ax_props['yscale'] = 'log'

        if ax_props['xlabel'] == 'cv':
            xmin = 0
            xmax = 1.05 * x.max()
            ax_props['xlim'] = (xmin, xmax)
        elif ax_props['ylabel'] == 'cv':
            ymin = 0
            ymax = 1.05 * y.max()
            ax_props['ylim'] = (ymin, ymax)

        if grid is not None:
            ax.grid(grid)

        ax.set(**ax_props)

        if legend:
            if np.isscalar(legend):
                ax.legend()
            else:
                ax.legend(**legend)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

    def plot_distributions(
            self,
            features,
            kind='violin',
            ax=None,
            tight_layout=True,
            legend=False,
            orientation='vertical',
            sort=False,
            bottom=0,
            grid=None,
            **kwargs):
        '''Plot distribution of spike-in controls

        Args:
            features (list or string): List of features to plot. If it is the \
                    string 'spikeins', plot all spikeins, if the string \
                    'other', plot other features.
            kind (string): Kind of plot, one of 'violin' (default), 'box', \
                    'swarm'.
            ax (matplotlib.axes.Axes): Axes to plot into. If None (default), \
                    create a new figure and axes.
            tight_layout (bool or dict): Whether to call \
                    matplotlib.pyplot.tight_layout at the end of the \
                    plotting. If it is a dict, pass it unpacked to that \
                    function.
            legend (bool or dict): If True, call ax.legend(). If a dict, \
                    pass as **kwargs to ax.legend. Notice that legend has a \
                    special meaning in these kinds of seaborn plots.
            orientation (string): 'horizontal' or 'vertical'.
            sort (bool or string): True or 'ascending' sorts the features by \
                    median, 'descending' uses the reverse order.
            bottom (float or string): The value of zero-count features. If \
                    you are using a log axis, you may want to set this to \
                    0.1 or any other small positive number. If a string, it \
                    must be 'pseudocount', then the CountsTable.pseudocount \
                    will be used.
            grid (bool or None): Whether to add a grid to the plot. None \
                    defaults to your existing settings.
            **kwargs: named arguments passed to the plot function.

        Return:
            matplotlib.axes.Axes: The axes with the plot.
        '''
        if ax is None:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(18, 8))

        counts = self.dataset.counts

        if features == 'spikeins':
            counts = counts.get_spikeins()
        elif features == 'other':
            counts = counts.get_other_features()
        else:
            counts = counts.loc[features]

        if sort:
            asc = sort != 'descending'
            ind = counts.median(axis=1).sort_values(ascending=asc).index
            counts = counts.loc[ind]

        if bottom == 'pseudocount':
            bottom = counts.pseudocount
        counts = np.maximum(counts, bottom)

        ax_props = {}
        if kind == 'violin':
            defaults = {
                    'scale': 'width',
                    'inner': 'stick',
                    }
            Plot._update_properties(kwargs, defaults)
            sns.violinplot(
                    data=counts.T,
                    orient=orientation,
                    ax=ax,
                    **kwargs)
        elif kind == 'box':
            defaults = {}
            Plot._update_properties(kwargs, defaults)
            sns.boxplot(
                    data=counts.T,
                    orient=orientation,
                    ax=ax,
                    **kwargs)
        elif kind == 'swarm':
            defaults = {}
            Plot._update_properties(kwargs, defaults)
            sns.swarmplot(
                    data=counts.T,
                    orient=orientation,
                    ax=ax,
                    **kwargs)
        else:
            raise ValueError('Plot kind not understood')

        if orientation == 'vertical':
            ax_props['ylim'] = (0.9 * bottom, 1.1 * counts.values.max())
            if not counts._normalized:
                ax_props['ylabel'] = 'Number of reads'
            elif counts._normalized != 'custom':
                ax_props['ylabel'] = counts._normalized.capitalize().replace('_', ' ')
            for label in ax.get_xmajorticklabels():
                label.set_rotation(90)
                label.set_horizontalalignment("center")
            ax.grid(True, 'y')
        elif orientation == 'horizontal':
            ax_props['xlim'] = (0.9 * bottom, 1.1 * counts.values.max())
            if not counts._normalized:
                ax_props['xlabel'] = 'Number of reads'
            elif counts._normalized != 'custom':
                ax_props['xlabel'] = counts._normalized.capitalize().replace('_', ' ')
            ax.grid(True, axis='x')

        ax.set(**ax_props)

        if grid is not None:
            ax.grid(grid)

        if legend:
            if np.isscalar(legend):
                ax.legend()
            else:
                ax.legend(**legend)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

        return ax

    def scatter_reduced(
            self,
            vectors_reduced,
            color_by=None,
            color_log=None,
            cmap='viridis',
            default_color='darkgrey',
            ax=None,
            tight_layout=True,
            high_on_top=False,
            **kwargs):
        '''Scatter samples or features after dimensionality reduction.

        Args:
            vectors_reduced (tuple of str or pandas.Dataframe): if a tuple of
                str, the names of the columns with the coordinates in the
                samplesheet or featuresheet. If a pandas.Dataframe, the matrix
                of coordinates of the samples/features in low dimensions. Rows
                are samples/features, columns (typically 2 or 3) are the
                component in the low-dimensional embedding.
            color_by (string or None): color sample dots by phenotype or
                expression of a certain feature.
            color_log (bool or None): use log of phenotype/expression in the
                colormap. Default None only logs expression, but not
                phenotypes.
            cmap (string or matplotlib colormap): color map to use for the
                sample dots. For categorical coloring, a palette with the
                right number of colors or more can be passed.
            ax (matplotlib.axes.Axes): The axes to plot into. If None
                (default), a new figure with one axes is created. ax must
                not strictly be a matplotlib class, but it must have
                common methods such as 'plot' and 'set'.
            default_color (str or matplotlib color): default color for missing
                categories, NaNs, and no coloring at all
            tight_layout (bool or dict): Whether to call
                matplotlib.pyplot.tight_layout at the end of the
                plotting. If it is a dict, pass it unpacked to that
                function.
            high_on_top (bool): Plot high expression/phenotype values on top.
                This argument is ignored for categorical phenotypes.
            **kwargs: named arguments passed to the plot function.

        Returns:
            matplotlib.axes.Axes with the axes containing the plot.

        NOTE: if a categorical colormap is used, the mapping of category to
        color is stored into ax._singlet_cmap.
        '''
        if isinstance(vectors_reduced, tuple):
            if pd.Index(vectors_reduced).isin(self.dataset.samplesheet.columns).all():
                vectors_reduced = self.dataset.samplesheet[list(vectors_reduced)]
                data = self.dataset.counts
                metadata = self.dataset.samplesheet
            elif pd.Index(vectors_reduced).isin(self.dataset.featuresheet.columns).all():
                vectors_reduced = self.dataset.featuresheet[list(vectors_reduced)]
                data = self.dataset.counts.T
                metadata = self.dataset.featuresheet
            else:
                raise ValueError('reduced_vectors is not consistent with samples nor features')
        else:
            if (vectors_reduced.index == self.dataset.samplesheet.index).all():
                data = self.dataset.counts
                metadata = self.dataset.samplesheet
            elif (vectors_reduced.index == self.dataset.featuresheet.index).all():
                data = self.dataset.counts.T
                metadata = self.dataset.featuresheet
            else:
                raise ValueError('reduced_vectors is not consistent with samples nor features')

        if ax is None:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(13, 8))

        defaults = {
                's': 90,
                }
        Plot._update_properties(kwargs, defaults)
        tiers = np.ones(vectors_reduced.shape[0])

        if color_by is None:
            kwargs['color'] = default_color
        else:
            if isinstance(cmap, str):
                cmap = cm.get_cmap(cmap)
            if color_by in metadata.columns:
                color_data = metadata.loc[:, color_by]
                if hasattr(color_data, 'cat'):
                    color_is_numeric = False
                else:
                    color_is_numeric = np.issubdtype(color_data.dtype, np.number)
                color_by_phenotype = True
            elif color_by in data.index:
                color_data = data.loc[color_by]
                color_is_numeric = True
                color_by_phenotype = False
            else:
                raise ValueError(
                    'The label '+color_by+' is neither a phenotype nor a feature')

            # Categorical columns get just a list or a dict of colors
            if (hasattr(color_data, 'cat')) or (not color_is_numeric):
                cd_unique = list(np.unique(color_data.values))
                if callable(cmap):
                    c_unique = cmap(np.linspace(0, 1, len(cd_unique)))
                elif isinstance(cmap, dict):
                    c_unique = np.asarray([cmap.get(x, default_color) for x in cd_unique])
                else:
                    c_unique = np.asarray(cmap)

                # Assign the actual colors to categories. Missing ones default
                c = c_unique[[cd_unique.index(x) for x in color_data.values]]

                # For categories, we have to tell the user about the mapping
                if not hasattr(ax, '_singlet_cmap'):
                    ax._singlet_cmap = {}
                ax._singlet_cmap.update(dict(zip(cd_unique, c_unique)))

            # Non-categorical numeric types are more tricky: check for NaNs
            else:
                if np.isnan(color_data.values).any():
                    unmask = ~np.isnan(color_data.values)
                else:
                    unmask = np.ones(len(color_data), bool)

                cd_min = color_data.values[unmask].min()
                cd_max = color_data.values[unmask].max()

                if color_log is None:
                    color_log = not color_by_phenotype

                if color_log:
                    if color_by_phenotype:
                        pc = 0.1 * cd_min
                    else:
                        pc = self.dataset.counts.pseudocount
                    color_data = np.log10(color_data + pc)
                    cd_min = np.log10(cd_min + pc)
                    cd_max = np.log10(cd_max + pc)

                cd_norm = (color_data.values - cd_min) / (cd_max - cd_min)

                if high_on_top:
                    tiers = pd.qcut(
                            cd_norm, np.linspace(0, 1, 5),
                            retbins=False, labels=False,
                            duplicates='drop',
                            )


                c = np.zeros((len(color_data), 4), float)
                c[unmask] = cmap(cd_norm[unmask])
                # Grey-ish semitransparency for NaNs
                c[~unmask] = mpl.colors.to_rgba(default_color, alpha=0.3)

            kwargs['c'] = c

        tiers_unique = np.sort(np.unique(tiers))
        for t in tiers_unique:
            ind = tiers == t
            vec = vectors_reduced.loc[ind]
            kw = dict(kwargs)
            if 'c' in kw:
                if (not isinstance(kw['c'], str)) and (len(kw['c']) == len(vec)):
                    kw['c'] = kw['c'][ind]
            if not np.isscalar(kw['s']):
                kw['s'] = kw['s'][ind]
            vec.plot(
                    x=vec.columns[0],
                    y=vec.columns[1],
                    kind='scatter',
                    ax=ax,
                    **kw)

        ax.grid(True)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

        return ax

    def scatter_reduced_samples(
            self,
            vectors_reduced,
            color_by=None,
            color_log=None,
            cmap='viridis',
            ax=None,
            tight_layout=True,
            **kwargs):
        '''Scatter samples after dimensionality reduction.

        Args:
            vectors_reduced (pandas.Dataframe): matrix of coordinates of the
                samples after dimensionality reduction. Rows are samples,
                columns (typically 2 or 3) are the component in the
                low-dimensional embedding.
            color_by (string or None): color sample dots by phenotype or
                expression of a certain feature.
            color_log (bool or None): use log of phenotype/expression in the
                colormap. Default None only logs expression, but not
                phenotypes.
            cmap (string or matplotlib colormap): color map to use for the
                sample dots. For categorical coloring, a palette with the
                right number of colors or more can be passed.
            ax (matplotlib.axes.Axes): The axes to plot into. If None
                (default), a new figure with one axes is created. ax must
                not strictly be a matplotlib class, but it must have
                common methods such as 'plot' and 'set'.
            tight_layout (bool or dict): Whether to call
                matplotlib.pyplot.tight_layout at the end of the
                plotting. If it is a dict, pass it unpacked to that
                function.
            **kwargs: named arguments passed to the plot function.

        Returns:
            matplotlib.axes.Axes with the axes containing the plot.
        '''
        return self.scatter_reduced(
            vectors_reduced=vectors_reduced,
            color_by=color_by,
            color_log=color_log,
            cmap=cmap,
            ax=ax,
            tight_layout=tight_layout,
            **kwargs,
            )

    def clustermap(
            self,
            cluster_samples=False,
            cluster_features=False,
            phenotypes_cluster_samples=(),
            phenotypes_cluster_features=(),
            annotate_samples=False,
            annotate_features=False,
            labels_samples=True,
            labels_features=True,
            orientation='horizontal',
            colorbars=False,
            **kwargs):
        '''Samples versus features / phenotypes.

        Args:
            cluster_samples (bool or linkage): Whether to cluster samples and
                    show the dendrogram. Can be either, False, True, or a
                    linkage from scipy.cluster.hierarchy.linkage.
            cluster_features (bool or linkage): Whether to cluster features
                    and show the dendrogram. Can be either, False, True, or a
                    linkage from scipy.cluster.hierarchy.linkage.
            phenotypes_cluster_samples (iterable of strings): Phenotypes to
                    add to the features for joint clustering of the samples.
                    If the clustering has been
                    precomputed including phenotypes and the linkage matrix
                    is explicitely set as cluster_samples, the *same*
                    phenotypes must be specified here, in the same order.
            phenotypes_cluster_features (iterable of strings): Phenotypes to
                    add to the features for joint clustering of the features
                    and phenotypes. If the clustering has been
                    precomputed including phenotypes and the linkage matrix
                    is explicitely set as cluster_features, the *same*
                    phenotypes must be specified here, in the same order.
            annotate_samples (dict, or False): Whether and how to
                    annotate the samples with separate colorbars. The
                    dictionary must have phenotypes or features as keys. For
                    qualitative phenotypes, the values can be palette names
                    or palettes (with at least as many colors as there are
                    categories). For quantitative phenotypes and features,
                    they can be colormap names or colormaps.
            annotate_features (dict, or False): Whether and how to
                    annotate the featues with separate colorbars. The
                    dictionary must have features metadata as keys. For
                    qualitative annotations, the values can be palette names
                    or palettes (with at least  as many colors as there are
                    categories). For quantitative annotatoins, the values
                    can be colormap names or colormaps. Keys must be columns
                    of the Dataset.featuresheet, except for the key 'mean
                    expression' which is interpreted to mean the average of
                    the counts for that feature.
            labels_samples (bool): Whether to show the sample labels. If you
                    have hundreds or more samples, you may want to turn this
                    off to make the plot tidier.
            labels_features (bool): Whether to show the feature labels. If you
                    have hundreds or more features, you may want to turn this
                    off to make the plot tidier.
            orientation (string): Whether the samples are on the abscissa
                    ('horizontal') or on the ordinate ('vertical').
            tight_layout (bool or dict): Whether to call
                    matplotlib.pyplot.tight_layout at the end of the
                    plotting. If it is a dict, pass it unpacked to that
                    function.
            colorbars (bool): Whether to add colorbars. One colorbar refers
                    to the heatmap. Moreover, if annotations for samples or
                    features are shown, a colorbar for each of them will be
                    shown as well.
            **kwargs: named arguments passed to seaborn.clustermap.

        Returns:
            A seaborn ClusterGrid instance.
        '''
        data = self.dataset.counts.copy()
        for pheno in phenotypes_cluster_features:
            data.loc[pheno] = self.dataset.samplesheet.loc[:, pheno]

        # FIXME: what to do with NaN?
        if cluster_samples is True:
            cluster_samples = self.dataset.cluster.hierarchical(
                    axis='samples',
                    phenotypes=phenotypes_cluster_samples,
                    )
            linkage_samples = cluster_samples['linkage']
        elif cluster_samples is False:
            linkage_samples = None
        else:
            linkage_samples = cluster_samples

        if cluster_features is True:
            cluster_features = self.dataset.cluster.hierarchical(
                    axis='features',
                    phenotypes=phenotypes_cluster_features,
                    )
            linkage_features = cluster_features['linkage']
        elif cluster_features is False:
            linkage_features = None
        else:
            linkage_features = cluster_features

        if annotate_samples:
            cbars_samples = []
            col_samples = []
            for key, val in annotate_samples.items():
                if key in self.dataset.samplesheet.columns:
                    color_data = self.dataset.samplesheet.loc[:, key]
                    is_numeric = np.issubdtype(color_data.dtype, np.number)
                    if (color_data.dtype.name == 'category') or (not is_numeric):
                        cmap_type = 'qualitative'
                    else:
                        cmap_type = 'sequential'
                else:
                    color_data = self.dataset.counts.loc[key]
                    cmap_type = 'sequential'

                if isinstance(val, str):
                    if cmap_type == 'qualitative':
                        cd_unique = list(np.unique(color_data.values))
                        n_colors = len(cd_unique)
                        palette = sns.color_palette(val, n_colors=n_colors)
                        c = [palette[cd_unique.index(x)] for x in color_data.values]
                        cbi = {'name': key, 'palette': palette,
                               'ticklabels': cd_unique,
                               'type': 'qualitative',
                               'n_colors': n_colors}
                    else:
                        cmap = cm.get_cmap(val)
                        vmax = np.nanmax(color_data.values)
                        vmin = np.nanmin(color_data.values)
                        cval = (color_data.values - vmin) / (vmax - vmin)
                        c = cmap(cval)
                        cbi = {'name': key, 'cmap': cmap,
                               'vmin': vmin, 'vmax': vmax,
                               'type': 'sequential'}
                else:
                    if cmap_type == 'qualitative':
                        cd_unique = list(np.unique(color_data.values))
                        n_colors = len(cd_unique)
                        if len(palette) < n_colors:
                            raise ValueError(
                            'Palettes must have as many colors as there are categories')
                        palette = val
                        c = [palette[cd_unique.index(x)] for x in color_data.values]
                        cbi = {'name': key, 'palette': palette[:n_colors],
                               'ticks': cd_unique,
                               'type': 'qualitative',
                               'n_colors': n_colors}
                    else:
                        cmap = val
                        vmax = np.nanmax(color_data.values)
                        vmin = np.nanmin(color_data.values)
                        cval = (color_data.values - vmin) / (vmax - vmin)
                        c = cmap(cval)
                        cbi = {'name': key, 'cmap': cmap,
                               'vmin': vmin, 'vmax': vmax,
                               'type': 'sequential'}

                col_samples.append(c)
                cbars_samples.append(cbi)

            col_samples = pd.DataFrame(
                    data=[list(a) for a in col_samples],
                    columns=color_data.index,
                    index=annotate_samples.keys()).T
        else:
            col_samples = None

        if annotate_features:
            cbars_features = []
            col_features = []
            for key, val in annotate_features.items():
                if key == 'mean expression':
                    color_data = self.dataset.counts.mean(axis=1)
                else:
                    color_data = self.dataset.featuresheet.loc[:, key]
                is_numeric = np.issubdtype(color_data.dtype, np.number)
                if (color_data.dtype.name == 'category') or (not is_numeric):
                    cmap_type = 'qualitative'
                else:
                    cmap_type = 'sequential'

                if isinstance(val, str):
                    if cmap_type == 'qualitative':
                        cd_unique = list(np.unique(color_data.values))
                        n_colors = len(cd_unique)
                        palette = sns.color_palette(val, n_colors=n_colors)
                        c = [palette[cd_unique.index(x)] for x in color_data.values]
                        cbi = {'name': key, 'palette': palette,
                               'ticklabels': cd_unique,
                               'type': 'qualitative',
                               'n_colors': n_colors}
                    else:
                        cmap = cm.get_cmap(val)
                        vmax = np.nanmax(color_data.values)
                        vmin = np.nanmin(color_data.values)
                        cval = (color_data.values - vmin) / (vmax - vmin)
                        c = cmap(cval)
                        cbi = {'name': key, 'cmap': cmap,
                               'vmin': vmin, 'vmax': vmax,
                               'type': 'sequential'}
                else:
                    if cmap_type == 'qualitative':
                        cd_unique = list(np.unique(color_data.values))
                        n_colors = len(cd_unique)
                        if len(palette) < n_colors:
                            raise ValueError(
                            'Palettes must have as many colors as there are categories')
                        palette = val
                        c = [palette[cd_unique.index(x)] for x in color_data.values]
                        cbi = {'name': key, 'palette': palette[:n_colors],
                               'ticks': cd_unique,
                               'type': 'qualitative',
                               'n_colors': n_colors}
                    else:
                        cmap = val
                        vmax = np.nanmax(color_data.values)
                        vmin = np.nanmin(color_data.values)
                        cval = (color_data.values - vmin) / (vmax - vmin)
                        c = cmap(cval)
                        cbi = {'name': key, 'cmap': cmap,
                               'vmin': vmin, 'vmax': vmax,
                               'type': 'sequential'}

                col_features.append(c)
                cbars_features.append(cbi)

            col_features = pd.DataFrame(
                    data=[list(a) for a in col_features],
                    columns=color_data.index,
                    index=annotate_features.keys()).T

        else:
            col_features = None

        if orientation == 'horizontal':
            row_linkage = linkage_features
            col_linkage = linkage_samples
            row_colors = col_features
            col_colors = col_samples
            row_labels = labels_features
            col_labels = labels_samples
            if not row_labels:
                ylabel = 'features'
            if not col_labels:
                xlabel = 'samples'
        elif orientation == 'vertical':
            data = data.T
            row_linkage = linkage_samples
            col_linkage = linkage_features
            row_colors = col_samples
            col_colors = col_features
            row_labels = labels_samples
            col_labels = labels_features
            if not row_labels:
                ylabel = 'samples'
            if not col_labels:
                xlabel = 'features'
        else:
            raise ValueError('Orientation must be "horizontal" or "vertical".')

        defaults = {
                'yticklabels': row_labels,
                'xticklabels': col_labels,
                'row_colors': row_colors,
                'col_colors': col_colors}

        if row_linkage is not None:
            defaults.update({
                'row_cluster': True,
                'row_linkage': row_linkage})
        else:
            defaults.update({'row_cluster': False})

        if col_linkage is not None:
            defaults.update({
                'col_cluster': True,
                'col_linkage': col_linkage})
        else:
            defaults.update({'col_cluster': False})

        Plot._update_properties(kwargs, defaults)

        g = sns.clustermap(
                data=data,
                **kwargs)

        ax = g.ax_heatmap
        for label in ax.get_xmajorticklabels():
            label.set_rotation(90)
            label.set_horizontalalignment("center")
        for label in ax.get_ymajorticklabels():
            label.set_rotation(0)
            label.set_verticalalignment("center")

        if not row_labels:
            ax.set_ylabel(ylabel)
        if not col_labels:
            ax.set_xlabel(xlabel)

        if colorbars:
            # The colorbar for the heatmap is shown anyway
            if col_samples is not None:
                n_cbars = len(cbars_samples)
                caxs = []
                if orientation == 'horizontal':
                    wcb = min(0.3, 0.4 / n_cbars)
                    xcb = 0.98 - wcb * n_cbars - 0.05 * (n_cbars - 1)
                else:
                    hcb = min(0.3, 0.4 / n_cbars)
                    ycb = 0.98 - hcb
                for i, cbi in enumerate(cbars_samples):
                    if orientation == 'horizontal':
                        cax = g.fig.add_axes((xcb, 0.955, wcb, 0.025))
                    else:
                        cax = g.fig.add_axes((0.01, ycb, 0.02, hcb))
                    caxs.append(cax)

                    kw = {}
                    if cbi['type'] == 'sequential':
                        kw['norm'] = mpl.colors.Normalize(
                                vmin=cbi['vmin'], vmax=cbi['vmax'])
                        cb = mpl.colorbar.ColorbarBase(
                                cax,
                                cmap=cbi['cmap'],
                                orientation=orientation,
                                **kw)
                    else:
                        n_colors = cbi['n_colors']
                        bounds = [1.0 * i / n_colors for i in range(n_colors + 1)]
                        ticks = [(2.0 * i + 1) / (n_colors * 2) for i in range(n_colors)]
                        kw['norm'] = mpl.colors.Normalize(vmin=0, vmax=1)
                        cmap = mpl.colors.ListedColormap(cbi['palette'])
                        cb = mpl.colorbar.ColorbarBase(
                                cax,
                                cmap=cmap,
                                boundaries=bounds,
                                ticks=ticks,
                                orientation=orientation,
                                **kw)
                        if orientation == 'horizontal':
                            cb.ax.set_xticklabels([str(x) for x in cbi['ticklabels']])
                        else:
                            cb.ax.set_yticklabels([str(x) for x in cbi['ticklabels']])

                    cb.set_label(cbi['name'])

                    if orientation == 'horizontal':
                        xcb += wcb + 0.05
                    else:
                        ycb -= hcb + 0.05

                if orientation == 'horizontal':
                    g.ax_cbars_columns = caxs
                else:
                    g.ax_cbars_rows = caxs

            if col_features is not None:
                n_cbars = len(cbars_features)
                caxs = []
                if orientation == 'horizontal':
                    orientation_cb = 'vertical'
                else:
                    orientation_cb = 'horizontal'
                if orientation_cb == 'horizontal':
                    wcb = min(0.3, 0.4 / n_cbars)
                    xcb = 0.98 - wcb * n_cbars - 0.05 * (n_cbars - 1)
                else:
                    hcb = min(0.3, 0.4 / n_cbars)
                    ycb = 0.98 - hcb
                for i, cbi in enumerate(cbars_features):
                    if orientation_cb == 'horizontal':
                        cax = g.fig.add_axes((xcb, 0.955, wcb, 0.025))
                    else:
                        cax = g.fig.add_axes((0.01, ycb, 0.02, hcb))
                    caxs.append(cax)

                    kw = {}
                    if cbi['type'] == 'sequential':
                        kw['norm'] = mpl.colors.Normalize(
                                vmin=cbi['vmin'], vmax=cbi['vmax'])
                        cb = mpl.colorbar.ColorbarBase(
                                cax,
                                cmap=cbi['cmap'],
                                orientation=orientation_cb,
                                **kw)
                    else:
                        n_colors = cbi['n_colors']
                        bounds = [1.0 * i / n_colors for i in range(n_colors + 1)]
                        ticks = [(2.0 * i + 1) / (n_colors * 2) for i in range(n_colors)]
                        kw['norm'] = mpl.colors.Normalize(vmin=0, vmax=1)
                        cmap = mpl.colors.ListedColormap(cbi['palette'])
                        cb = mpl.colorbar.ColorbarBase(
                                cax,
                                cmap=cmap,
                                boundaries=bounds,
                                ticks=ticks,
                                orientation=orientation_cb,
                                **kw)
                        if orientation_cb == 'horizontal':
                            cb.ax.set_xticklabels([str(x) for x in cbi['ticklabels']])
                        else:
                            cb.ax.set_yticklabels([str(x) for x in cbi['ticklabels']])

                    cb.set_label(cbi['name'])

                    if orientation_cb == 'horizontal':
                        xcb += wcb + 0.05
                    else:
                        ycb -= hcb + 0.05

                if orientation_cb == 'horizontal':
                    g.ax_cbars_columns = caxs
                else:
                    g.ax_cbars_rows = caxs

        else:
            # Remove colorbar
            g.fig.get_axes()[-1].remove()

        # TODO: reimplement some heuristic tight_layout

        return g

    def dot_plot(
            self,
            group_axis='samples',
            group_by=None,
            group_order=None,
            plot_list=None,
            color_log=None,
            vmin='min',
            vmax='max',
            threshold=10,
            min_size=2,
            layout='horizontal',
            cmap='plasma',
            ax=None,
            tight_layout=True,
            **kwargs):
        '''Group samples and plot fraction and levels of counts.

        For every group, the size of the dot indicates the fraction of samples
        in that group with counts above threshold, while the color indicates
        the average counts within the group.

        Args:
            group_axis (str): It must be 'samples' or 'features'. The former
                looks at feature counts within sample groups, the latter at
                sample counts within feature groups.
            group_by (string or None): group samples/features by metadata.
            group_order (list or None): an optional order of the groups. If
                None, an automatic order will be used.
            plot_list (list of str): the features/samples to plot.
            color_log (bool or None): use log of phenotype/expression in the
                colormap. Default None only logs expression, but not
                phenotypes.
            vmin (str or float): minimum value to scale the coloring
                with. If this is a string, it must be one of 'min' (minimum
                across plot_list), 'min_single' (minimum for each element of
                plot_list). If a float, it is used as the minimum.
            vmax (str or float): maximum value to scale the coloring
                with. If this is a string, it must be one of 'max' (maximum
                across plot_list), 'max_single' (maximum for each element of
                plot_list). If a float, it is used as the maximum.
            threshold (float): a features/sample is considered if >= this
                value.
            min_size (float): the minimal size of a dot in the plot.
            layout (str): 'horizontal' or 'vertical'. The former has groups as
                rows, the latter as columns.
            cmap (string or matplotlib colormap): color map to use for the
                sample dots. For categorical coloring, a palette with the
                right number of colors or more can be passed.
            ax (matplotlib.axes.Axes): The axes to plot into. If None
                (default), a new figure with one axes is created. ax must
                not strictly be a matplotlib class, but it must have
                common methods such as 'plot' and 'set'.
            tight_layout (bool or dict): Whether to call
                matplotlib.pyplot.tight_layout at the end of the
                plotting. If it is a dict, pass it unpacked to that
                function.
            **kwargs: named arguments passed to the plot function.

        Returns:
            matplotlib.axes.Axes with the axes containing the plot.

        NOTE: the mappings of fraction to size and count level to color are
        stored into ax._singlet_dotmap.
        '''

        if ax is None:
            new_axes = True
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 8))
        else:
            new_axes = False

        defaults = {}
        Plot._update_properties(kwargs, defaults)

        def size_fun(fraction):
            return min_size + (fraction * 11)**2

        if group_axis == 'samples':
            countnames = self.dataset.featurenames
            plot_listc = [p for p in plot_list if p in countnames]
            data = self.dataset.counts.loc[plot_listc].fillna(0).T
            for count in plot_list:
                if count not in data.columns:
                    data[count] = self.dataset.samplesheet[count]
            data = data.loc[:, plot_list]
            data[group_by] = self.dataset.samplesheet[group_by]
        else:
            countnames = self.dataset.samplenames
            plot_listc = [p for p in plot_list if p in countnames]
            data = self.dataset.counts.loc[:, plot_listc].fillna(0)
            for count in plot_list:
                if count not in data.columns:
                    data[count] = self.dataset.featuresheet[count]
            data = data.loc[:, plot_list]
            data[group_by] = self.dataset.featuresheet[group_by]

        if group_order is None:
            groups = list(set(data[group_by]))
        else:
            groups = list(group_order)
        points = []
        for ig, count in enumerate(plot_list):
            gexist = data[group_by].unique()
            gby = data[[count, group_by]].groupby(group_by)
            clog = color_log or ((color_log is None) and (count in plot_listc))
            for ct in groups:
                if ct not in gexist:
                    continue
                dfi = gby.get_group(ct)
                frac_exp = (dfi[count] >= threshold).mean()
                if clog:
                    mean_exp = np.log10(dfi[count].values + self.dataset.counts.pseudocount).mean()
                else:
                    mean_exp = dfi[count].values.mean()
                point = {
                    'fraction': frac_exp,
                    'level': mean_exp,
                    'group': ct,
                    'count': count,
                    }
                if layout == 'horizontal':
                    point['x'] = ig
                    point['y'] = groups.index(ct)
                elif layout == 'vertical':
                    point['x'] = groups.index(ct)
                    point['y'] = ig
                else:
                    raise ValueError(
                            'Layout must be "horizontal" or "vertical"')
                points.append(point)

        points = pd.DataFrame(points)
        points.set_index(['count', 'group'], inplace=True, drop=False)

        # Set size and color based on fraction and level
        points['s'] = 0.0
        points['c'] = 0.0
        for count in plot_list:
            if vmin == 'min':
                vm = points['level'].values.min()
            elif vmin == 'min_single':
                vm = points.loc[points['count'] == count, 'level'].values.min()
            else:
                vm = vmin

            if vmax == 'max':
                vM = points['level'].values.max()
            elif vmax == 'max_single':
                vM = points.loc[points['count'] == count, 'level'].values.max()
            else:
                vM = vmax

            for gr in groups:
                if gr not in gexist:
                    continue
                size = size_fun(points.at[(count, gr), 'fraction'])
                shade = (points.at[(count, gr), 'level'] - vm) / (vM - vm)
                points.at[(count, gr), 's'] = size
                points.at[(count, gr), 'c'] = shade

        if isinstance(cmap, str):
            cmap = cm.get_cmap(cmap)

        ax.scatter(
            points['x'].values,
            points['y'].values,
            s=points['s'].values,
            c=cmap(points['c'].values),
            )
        if layout == 'horizontal':
            ax.set_xticks(np.arange(len(plot_list)))
            ax.set_xticklabels(plot_list)
            ax.set_yticks(np.arange(len(groups)))
            ax.set_yticklabels(groups)
            ax.set_xlim(-0.5, len(plot_list) - 0.5)
            ax.set_ylim(-0.5, len(groups) - 0.5)
        else:
            ax.set_yticks(np.arange(len(plot_list)))
            ax.set_yticklabels(plot_list)
            ax.set_xticks(np.arange(len(groups)))
            ax.set_xticklabels(groups)
            ax.set_ylim(-0.5, len(plot_list) - 0.5)
            ax.set_xlim(-0.5, len(groups) - 0.5)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

        if not hasattr(ax, '_singlet_dotmap'):
            ax._singlet_dotmap = {
                'fraction_size_map': size_fun,
                'level_color_map': cmap,
                }

        return ax

    def plot_group_abundance_changes(
            self,
            groupby,
            along,
            kind='number',
            group_order=None,
            along_order=None,
            scatter=True,
            interpolate=False,
            cmap=None,
            scatter_kwargs=None,
            interpolate_kwargs=None,
            ax=None,
            log=False,
            ymin=0,
            tight_layout=True,
            legend=False,
            ):
        '''Plot changes in sample abundance groups (e.g. in time)

        Args:
            groupby (string): column of the SampleSheet to group samples by
            along (string): column of the SampleSheet to plot abundances along
            kind (string): 'number', 'fraction', or 'percent' based on what
                kind of normalization across groups is requested
            group_order (sequence or None): optional sequence of values found
                within the "groupby" column to decide the order of the legend
            along_order (sequence or None): optional sequence of values found
                within the "along" column to decide the order of the dots
            scatter (bool): whether to show the scatter plot
            interpolate (bool): whether to show a monotonic spline
                interpolation between subsequent values in the "along" column
            cmap (dict, list, or None): a dictionary or a list of colors to
                plot the different groups. If a list, colors are paired to
                groups in the same order (see "group_order" argument)
            scatter_kwargs (dict or None): additional keyword arguments for the
                scatter plot
            interpolate_kwargs (dict or None): additional keyword arguments for
                the line plot of the interpolation
            ax (matplotlib.axes.Axes): The axes to plot into. If None
                (default), a new figure with one axes is created. ax must
                not strictly be a matplotlib class, but it must have
                common methods such as 'plot' and 'set'.
            log (False or float): whether to log the abundances. If not False,
                sets the base of the logarithm
            ymin (float): pseudocount to enable logarithmic plots of abundance
                as opposed to the default 0
            tight_layout (bool or dict): Whether to call
                matplotlib.pyplot.tight_layout at the end of the
                plotting. If it is a dict, pass it unpacked to that function.
            legend (bool or dict): If True, call ax.legend(). If a dict, pass
                as **kwargs to ax.legend.
        Returns:
            matplotlib.pyplot axes with the abundance changes
        '''
        from scipy import interpolate

        data = self.dataset.samplesheet[[groupby, along]].copy()
        data['__count__'] = 1
        data = (data.groupby([groupby, along])
                    .count()
                    .loc[:, '__count__']
                    .unstack(fill_value=0))

        if kind == 'fraction':
            data = 1.0 * data / data.sum(axis=0)
        elif kind == 'percent':
            data = 100.0 * data / data.sum(axis=0)
        elif kind != 'number':
            raise ValueError('kind not supported')

        data = np.maximum(data, ymin)

        if log:
            data = np.log(data) / np.log(log)

        if ax is None:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(13, 8))

        if group_order is not None:
            data = data.loc[group_order]

        if along_order is not None:
            data = data.loc[:, along_order]

        x = np.arange(data.shape[1])
        xorder = data.columns
        gorder = data.index

        for ig, go in enumerate(gorder):
            y = data.loc[go]

            kwargs = {}
            if isinstance(cmap, dict):
                kwargs['color'] = cmap[go]
            elif cmap is not None:
                kwargs['color'] = cmap[ig]

            sc_kwargs = kwargs.copy()
            sc_kwargs.update(scatter_kwargs)

            ax.scatter(
                    x, y,
                    label=go,
                    **sc_kwargs,
                    )

            if interpolate:
                outx = np.linspace(x[0], x[-1], 100)
                outy = interpolate.pchip_interpolate(x, y, outx)

                in_kwargs = kwargs.copy()
                in_kwargs.update(interpolate_kwargs)

                ax.plot(outx, outy,
                        **in_kwargs,
                        )

        ax.set_xticks(x)
        ax.set_xticklabels(xorder)
        ax.set_xlabel(along)
        ax.set_ylabel('{:} of samples'.format(kind.capitalize()))

        if legend:
            if np.isscalar(legend):
                ax.legend()
            else:
                ax.legend(**legend)

        if tight_layout:
            if isinstance(tight_layout, dict):
                plt.tight_layout(**tight_layout)
            else:
                plt.tight_layout()

        return ax
