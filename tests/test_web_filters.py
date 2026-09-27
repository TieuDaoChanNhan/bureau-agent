"""Shared T25 browser cases, inherited by both demo browser suites in CI.

This mixin deliberately has no unittest.TestCase base: the hosts provide the
browser and local HTTP server. Importing it needs neither Playwright nor keys.
"""


class IssueFilterChecks:
    def wait_for_filter_console(self, page):
        # Summaries arrive before the final outbox request and first render.
        page.wait_for_function("document.querySelector('#filterCount').textContent.startsWith('Showing ')")

    def seed_filter_cases(self, page):
        """Deterministic console inputs spanning all display statuses and kinds."""
        page.evaluate("""() => {
          const issue = (id, kind, title, status='open', details={}) => ({
            id, kind, title, status, details, blocking: false, subject_ids: [], depends_on: []});
          const action = (id, issue_id, action_type, extra={}) => ({id, issue_id, action_type,
            event_id: 'hackathon', title: 'A saved decision', description: '', payload: {},
            confidence: null, checks: [], evidence: [], trace: [], requires_approval: true, ...extra});
          const issues = [
            issue('new', 'unprocessed_message', 'New Discord message from Camille', 'open',
                  {text: 'x'.repeat(150) + ' Règlement et livraison'}),
            issue('proposed', 'unprocessed_message', 'New email message from René', 'proposed',
                  {text: 'Règlement du hackathon'}),
            issue('human', 'unprocessed_message', 'New Discord message from Alex', 'needs_human',
                  {text: 'Une exception au règlement'}),
            issue('identity', 'unmatched_payment', 'Payment needing confirmation', 'proposed'),
            issue('waiting', 'rooms_unassigned', 'Rooms waiting for planning'),
            issue('failed', 'multiple_group_membership', 'Team investigation failed', 'agent_failed'),
            issue('resolved', 'unprocessed_message', 'Resolved Discord question', 'resolved', {text: 'Resolved keyword'}),
            issue('dismissed', 'unprocessed_message', 'Dismissed email question', 'dismissed'),
            issue('other', 'unknown_kind', 'Unclassified issue'),
          ];
          issues[3].blocking = true;
          issues[4].depends_on = ['new'];
          const actions = [action('ap', 'proposed', 'SEND_MESSAGE'), action('ah', 'human', 'ESCALATE'),
            action('ai', 'identity', 'LINK_PAYMENT', {confidence: 0.8}),
            action('gone', 'unmatched_payment:old', 'LINK_PAYMENT', {title: 'Linked old payment', payload: {text: 'Archived receipt'}})];
          store({...summary('hackathon'), issues, actions, counts: {blocking: 1, non_blocking: 6}, safe_replies: []});
          ui.current = 'hackathon'; ui.sel.hackathon = 'issue:new'; ui.view = 'issue'; render();
        }""")

    def filter_keys(self, page):
        return page.locator('#issues .issue').evaluate_all('(rows) => rows.map(row => row.dataset.key)')

    def test_filters_intersect_status_kind_and_full_message_search(self):
        page = self.filter_page()
        self.seed_filter_cases(page)
        before = page.evaluate("JSON.stringify(ui.summaries)")
        kpis = page.locator('#kpis').inner_text()
        page.get_by_label('Search issues', exact=True).fill('DISCORD reglement')
        self.assertEqual(['issue:new', 'issue:human'], self.filter_keys(page))
        self.assertNotIn('Règlement', page.locator('[data-key="issue:new"] .m').inner_text())
        page.locator('[data-filter-status="human"]').click()
        self.assertEqual(['issue:human'], self.filter_keys(page))
        page.get_by_label('Kind', exact=True).select_option('payments')
        self.assertEqual([], self.filter_keys(page))
        self.assertIn('No issues match', page.locator('#issues').inner_text())
        self.assertEqual('Showing 0 of 10 issues', page.locator('#filterCount').inner_text())
        self.assertEqual(kpis, page.locator('#kpis').inner_text())
        self.assertEqual(before, page.evaluate('JSON.stringify(ui.summaries)'))
        page.get_by_role('button', name='Clear filters', exact=True).click()
        self.assertEqual(10, len(self.filter_keys(page)))
        page.get_by_label('Search issues', exact=True).fill('RENE')
        self.assertEqual(['issue:proposed'], self.filter_keys(page))

    def test_filters_cover_each_status_and_completed_actions(self):
        page = self.filter_page()
        self.seed_filter_cases(page)
        expected = {
            'human': ['issue:identity', 'issue:human'], 'proposed': ['issue:proposed'],
            'new': ['issue:new', 'issue:other'], 'waiting': ['issue:waiting'],
            'failed': ['issue:failed'], 'done': ['action:gone', 'issue:resolved', 'issue:dismissed'],
        }
        for status, keys in expected.items():
            with self.subTest(status=status):
                page.locator(f'[data-filter-status="{status}"]').click()
                self.assertEqual(keys, self.filter_keys(page))
                self.assertEqual('true', page.locator(f'[data-filter-status="{status}"]').get_attribute('aria-pressed'))
        self.assertTrue(page.locator('details.done').evaluate('el => el.open'))
        page.get_by_label('Kind', exact=True).select_option('payments')
        page.get_by_label('Search issues', exact=True).fill('archived receipt')
        self.assertEqual(['action:gone'], self.filter_keys(page))
        self.assertTrue(page.locator('[data-key="action:gone"]').is_visible())
        page.get_by_role('button', name='Clear filters', exact=True).click()
        for kind, keys in {'teams': ['issue:failed'], 'logistics': ['issue:waiting'], 'other': ['issue:other']}.items():
            page.get_by_label('Kind', exact=True).select_option(kind)
            self.assertEqual(keys, self.filter_keys(page))

    def test_filters_remember_preferences_without_cross_browser_state(self):
        page = self.filter_page()
        page.locator('[data-filter-status="new"]').click()
        page.get_by_label('Kind', exact=True).select_option('messages')
        page.get_by_label('Search issues', exact=True).fill('Discord')
        expected = self.filter_keys(page)
        self.assertTrue(expected)
        page.reload()
        self.wait_for_filter_console(page)
        self.assertEqual(expected, self.filter_keys(page))
        self.assertEqual('Discord', page.locator('#issueSearch').input_value())
        self.assertEqual('messages', page.locator('#issueKind').input_value())
        self.assertEqual('true', page.locator('[data-filter-status="new"]').get_attribute('aria-pressed'))
        page.locator('.issue-panel').screenshot(path=str(self.filter_artifacts / f't25-{type(self).__name__}-filters-desktop.png'))
        page.locator('[data-ev="wei"]').click()
        page.wait_for_function("ui.current === 'wei' && summary().id === 'wei'")
        self.assertEqual('Discord', page.locator('#issueSearch').input_value())
        private = page.context.browser.new_context()
        self.addCleanup(private.close)
        other = private.new_page()
        other.goto(page.url)
        self.wait_for_filter_console(other)
        self.assertEqual('', other.locator('#issueSearch').input_value())
        self.assertEqual('all', other.locator('#issueKind').input_value())

    def test_filters_recover_from_malformed_or_blocked_storage(self):
        page = self.filter_page()
        for stored in ('{broken', 'null', '42', '{"status":"__proto__","kind":{},"search":[]}'):
            with self.subTest(stored=stored):
                page.evaluate('(value) => localStorage.setItem(FILTER_KEY, value)', stored)
                page.reload()
                self.wait_for_filter_console(page)
                self.assertEqual({'status': 'all', 'kind': 'all', 'search': ''}, page.evaluate('ui.issueFilters'))
        page.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new Error('Storage blocked');}});")
        page.reload()
        self.wait_for_filter_console(page)
        page.get_by_label('Search issues', exact=True).fill('discord')
        page.locator('[data-filter-status="new"]').click()
        self.assertTrue(self.filter_keys(page))
        self.assertEqual('discord', page.evaluate('ui.issueFilters.search'))

    def test_filters_preserve_edits_and_do_not_restrict_event_actions(self):
        page = self.filter_page()
        page.evaluate("""async () => {
          store(await api('/api/events/hackathon/run?issue_id=message:m02', {method:'POST'}));
          ui.sel.hackathon = 'issue:message:m02'; render();
        }""")
        page.locator('[data-act="edit"]').click()
        page.locator('#draft').fill('An unsaved organizer draft.')
        baseline = page.evaluate('({queue: runnableIds(summary()), safe: summary().safe_replies, selection: ui.sel[ui.current]})')
        page.get_by_label('Search issues', exact=True).fill('no-results-t25')
        self.assertEqual([], self.filter_keys(page))
        self.assertTrue(page.locator('#filteredSelection').is_visible())
        self.assertEqual('An unsaved organizer draft.', page.locator('#draft').inner_text())
        self.assertEqual('true', page.locator('#draft').get_attribute('contenteditable'))
        self.assertEqual(baseline, page.evaluate('({queue: runnableIds(summary()), safe: summary().safe_replies, selection: ui.sel[ui.current]})'))
        page.get_by_role('button', name='Clear filters', exact=True).click()
        self.assertTrue(page.locator('#filteredSelection').is_hidden())
        self.assertEqual('An unsaved organizer draft.', page.locator('#draft').inner_text())

    def test_filters_follow_agent_approval_and_dependency_updates(self):
        page = self.filter_page()
        page.locator('[data-key="issue:message:m02"]').click()
        title = page.locator('[data-key="issue:message:m02"] .t').inner_text()
        page.locator('#issueSearch').fill(title)
        page.locator('[data-filter-status="new"]').click()
        self.assertEqual(['issue:message:m02'], self.filter_keys(page))
        page.locator('[data-act="retry"]').click()
        page.wait_for_function("!ui.busy && summary().actions.some(a => a.issue_id === 'message:m02')")
        self.assertEqual([], self.filter_keys(page))
        page.locator('[data-filter-status="proposed"]').click()
        self.assertEqual(['issue:message:m02'], self.filter_keys(page))
        page.locator('[data-act="approve"]').click()
        page.wait_for_function("!ui.busy && summary().issues.some(i => i.id === 'message:m02' && i.status === 'resolved')")
        self.assertEqual([], self.filter_keys(page))
        page.locator('[data-filter-status="done"]').click()
        self.assertTrue(page.locator('[data-key="issue:message:m02"]').is_visible())
        page.locator('#clearIssueFilters').click()
        self.seed_filter_cases(page)
        page.locator('[data-filter-status="waiting"]').click()
        self.assertEqual(['issue:waiting'], self.filter_keys(page))
        page.evaluate("summary().issues.find(i => i.id === 'new').status = 'resolved'; render();")
        self.assertEqual([], self.filter_keys(page))

    def test_filters_keyboard_and_400px_layout(self):
        page = self.filter_page()
        page.set_viewport_size({'width': 400, 'height': 900})
        search = page.get_by_label('Search issues', exact=True)
        search.focus()
        search.press_sequentially('discord')
        self.assertEqual('issueSearch', page.evaluate('document.activeElement.id'))
        self.assertEqual(7, page.locator('[data-filter-status]').count())
        search.press('Tab')
        self.assertEqual('all', page.evaluate('document.activeElement.dataset.filterStatus'))
        page.keyboard.press('Tab')
        page.keyboard.press('Space')
        self.assertEqual('human', page.evaluate('ui.issueFilters.status'))
        self.assertEqual('human', page.evaluate('document.activeElement.dataset.filterStatus'))
        self.assertNotEqual('none', page.evaluate('getComputedStyle(document.activeElement).outlineStyle'))
        page.keyboard.press('Enter')
        self.assertEqual('human', page.evaluate('ui.issueFilters.status'))
        # Tab across the remaining status buttons to the native select, then Clear.
        for _ in range(6):
            page.keyboard.press('Tab')
        self.assertEqual('issueKind', page.evaluate('document.activeElement.id'))
        page.keyboard.press('ArrowDown')
        self.assertEqual('payments', page.locator('#issueKind').input_value())
        page.keyboard.press('Tab')
        self.assertEqual('clearIssueFilters', page.evaluate('document.activeElement.id'))
        page.keyboard.press('Enter')
        self.assertEqual('issueSearch', page.evaluate('document.activeElement.id'))
        self.assertEqual('', search.input_value())
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= 400'))
        for selector in ('#issueSearch', '#issueKind', '#issueStatuses', '#clearIssueFilters'):
            box = page.locator(selector).bounding_box()
            self.assertGreaterEqual(box['x'], 0)
            self.assertLessEqual(box['x'] + box['width'], 400)
        page.locator('#issueSearch').fill('Discord')
        page.locator('#issueFilters').screenshot(path=str(self.filter_artifacts / f't25-{type(self).__name__}-filters-400.png'))

    def test_filters_do_not_execute_search_markup(self):
        page = self.filter_page()
        page.get_by_label('Search issues', exact=True).fill('<img src=x onerror="window.filterXss=true">')
        self.assertEqual([], self.filter_keys(page))
        self.assertFalse(page.evaluate('!!window.filterXss'))
        self.assertEqual(0, page.locator('#issues img').count())

    def test_filters_are_suspended_during_tours_and_restored_on_exit(self):
        page = self.filter_page()
        page.get_by_label('Search issues', exact=True).fill('no-results-t25')
        page.locator('[data-filter-status="failed"]').click()
        saved = page.evaluate('localStorage.getItem(FILTER_KEY)')
        page.locator('#heroTourBtn').click()
        page.locator('.driver-popover-title').wait_for()
        self.assertTrue(page.evaluate('ui.filtersSuspended'))
        self.assertEqual('', page.locator('#issueSearch').input_value())
        self.assertTrue(self.filter_keys(page))
        self.assertTrue(page.locator('#issueSearch').is_disabled())
        page.keyboard.press('Escape')
        page.wait_for_function('tourState.driver === null')
        self.assertEqual([], self.filter_keys(page))
        self.assertEqual('no-results-t25', page.locator('#issueSearch').input_value())
        self.assertEqual(saved, page.evaluate('localStorage.getItem(FILTER_KEY)'))
